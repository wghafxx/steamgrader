import asyncio
from contextlib import suppress
from fastapi import FastAPI, APIRouter, Query, Request, Response, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel
import os
import re
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from urllib.parse import urlencode
import uuid
import jwt
import httpx
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Steam OpenID config
JWT_SECRET = os.environ['JWT_SECRET']
PUBLIC_BASE_URL = os.environ['PUBLIC_BASE_URL'].rstrip('/')
STEAM_API_KEY = os.environ.get('STEAM_API_KEY')
logging.getLogger("httpx").setLevel(logging.WARNING)
OPENID_ENDPOINT = "https://steamcommunity.com/openid/login"
STEAM_SUMMARY_ENDPOINT = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"

# One entry per collection: every field a route filters, sorts or dedupes on. Add the index in the same edit as the query.
INDEXES: dict[str, list[IndexModel]] = {
    "status_checks": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("timestamp", DESCENDING)], name="timestamp_desc"),
    ],
    "users": [
        IndexModel([("steamid", ASCENDING)], name="steamid", unique=True),
    ],
    "chat_messages": [
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
        IndexModel([("steamid", ASCENDING), ("created_at", DESCENDING)], name="steamid_created_at"),
    ],
    "notifications": [
        IndexModel([("steamid", ASCENDING), ("created_at", DESCENDING)], name="steamid_created_at"),
        IndexModel([("steamid", ASCENDING), ("read", ASCENDING)], name="steamid_read"),
    ],
    "presence": [
        IndexModel([("visitor_id", ASCENDING)], name="visitor_id", unique=True),
        IndexModel([("last_seen", ASCENDING)], name="last_seen_ttl", expireAfterSeconds=120),
    ],
}


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:  # one at a time so a bad spec skips only itself
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:  # never block boot on an index; the log line names what to fix
                logging.getLogger(__name__).error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(limit: int = Query(20, ge=1, le=100)):
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


class OnlinePing(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$")


@api_router.post("/online/ping")
async def online_ping(body: OnlinePing):
    now = datetime.now(timezone.utc)
    await db.presence.update_one(
        {"visitor_id": body.visitor_id}, {"$set": {"last_seen": now}}, upsert=True
    )
    online = await db.presence.count_documents({"last_seen": {"$gte": now - timedelta(seconds=45)}})
    return {"online": online}


# ---------------- Steam OpenID auth ----------------

def _make_jwt(steamid: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": steamid, "iat": now, "exp": now + timedelta(days=7)},
        JWT_SECRET, algorithm="HS256",
    )


def _steamid_from_claimed_id(claimed_id: str) -> str:
    prefix = "https://steamcommunity.com/openid/id/"
    alt = "http://steamcommunity.com/openid/id/"
    for p in (prefix, alt):
        if claimed_id.startswith(p):
            steamid = claimed_id[len(p):]
            if steamid.isdigit() and len(steamid) <= 20:
                return steamid
    raise HTTPException(400, "Invalid Steam Claimed ID")


@api_router.get("/auth/steam")
async def steam_login():
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"{PUBLIC_BASE_URL}/api/auth/steam/callback",
        "openid.realm": PUBLIC_BASE_URL + "/",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return RedirectResponse(f"{OPENID_ENDPOINT}?{urlencode(params)}")


@api_router.get("/auth/steam/callback")
async def steam_callback(request: Request):
    received = dict(request.query_params)
    if received.get("openid.mode") != "id_res":
        return RedirectResponse(f"{PUBLIC_BASE_URL}/?login=cancelled", status_code=303)
    if received.get("openid.return_to") != f"{PUBLIC_BASE_URL}/api/auth/steam/callback":
        raise HTTPException(400, "Invalid OpenID return_to")

    steamid = _steamid_from_claimed_id(received.get("openid.claimed_id", ""))

    verification = {k: v for k, v in received.items() if k.startswith("openid.")}
    verification["openid.mode"] = "check_authentication"
    async with httpx.AsyncClient(timeout=10.0) as http:
        result = await http.post(OPENID_ENDPOINT, data=verification)
        if result.status_code != 200 or "is_valid:true" not in result.text.replace(" ", ""):
            return RedirectResponse(f"{PUBLIC_BASE_URL}/?login=failed", status_code=303)

        nickname, avatar, profile_url = "Steam User", None, None
        if STEAM_API_KEY:
            prof = await http.get(STEAM_SUMMARY_ENDPOINT, params={"key": STEAM_API_KEY, "steamids": steamid})
            if prof.status_code == 200:
                players = prof.json().get("response", {}).get("players", [])
                if players:
                    p = players[0]
                    nickname = p.get("personaname", nickname)
                    avatar = p.get("avatarfull") or p.get("avatarmedium") or p.get("avatar")
                    profile_url = p.get("profileurl")

    await db.users.update_one(
        {"steamid": steamid},
        {"$set": {
            "steamid": steamid, "nickname": nickname, "avatar": avatar,
            "profile_url": profile_url, "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    response = RedirectResponse(f"{PUBLIC_BASE_URL}/?login=ok", status_code=303)
    response.set_cookie(
        "session", _make_jwt(steamid), httponly=True, secure=True,
        samesite="lax", max_age=7 * 24 * 60 * 60, path="/",
    )
    return response


@api_router.get("/auth/me")
async def auth_me(request: Request):
    token = request.cookies.get("session")
    if not token:
        return {"user": None}
    try:
        steamid = jwt.decode(token, JWT_SECRET, algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        return {"user": None}
    user = await db.users.find_one({"steamid": steamid}, {"_id": 0, "updated_at": 0})
    return {"user": user}


@api_router.post("/auth/logout")
async def auth_logout(response: Response):
    response.delete_cookie("session", path="/")
    return {"ok": True}


# ---------------- Community chat ----------------

LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|discord\.gg|\b[\w-]+\.(?:com|ru|net|org|io|gg|me|xyz|top|pro|bet|casino|kz|ua|by|su|рф|info|biz|site|online|club|fun|app|cc|co|tv|ly|link|shop|win|vip)\b)",
    re.IGNORECASE,
)
REPEAT_RE = re.compile(r"(.)\1{9,}")
CHAT_COOLDOWN_SECONDS = 3


class ChatMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=300)


async def _current_user(request: Request) -> dict:
    token = request.cookies.get("session")
    try:
        steamid = jwt.decode(token or "", JWT_SECRET, algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        raise HTTPException(401, "Войдите через Steam")
    user = await db.users.find_one({"steamid": steamid}, {"_id": 0})
    if not user:
        raise HTTPException(401, "Войдите через Steam")
    return user


@api_router.get("/chat/messages")
async def chat_list(request: Request, limit: int = Query(50, ge=1, le=100)):
    await _current_user(request)
    docs = await db.chat_messages.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    for d in docs:
        d["created_at"] = d["created_at"].replace(tzinfo=timezone.utc).isoformat()
    return {"messages": docs[::-1]}


@api_router.post("/chat/messages")
async def chat_send(body: ChatMessageCreate, request: Request):
    user = await _current_user(request)
    text = " ".join(body.text.split())
    if not text:
        raise HTTPException(400, "Пустое сообщение")
    if LINK_RE.search(text) or LINK_RE.search(re.sub(r"\s*\.\s*", ".", text)):
        raise HTTPException(400, "Ссылки в чате запрещены")
    if REPEAT_RE.search(text):
        raise HTTPException(400, "Сообщение похоже на спам")

    now = datetime.now(timezone.utc)
    last = await db.chat_messages.find_one({"steamid": user["steamid"]}, sort=[("created_at", -1)])
    if last:
        age = (now - last["created_at"].replace(tzinfo=timezone.utc)).total_seconds()
        if age < CHAT_COOLDOWN_SECONDS:
            raise HTTPException(429, "Слишком часто. Подождите пару секунд")
        if age < 60 and last["text"].lower() == text.lower():
            raise HTTPException(400, "Не повторяйте одно и то же сообщение")

    doc = {
        "id": str(uuid.uuid4()), "steamid": user["steamid"], "nickname": user["nickname"],
        "avatar": user.get("avatar"), "text": text, "created_at": now,
    }
    await db.chat_messages.insert_one(dict(doc))
    doc["created_at"] = now.isoformat()
    return doc


# ---------------- Notifications ----------------

@api_router.get("/notifications")
async def notifications_list(request: Request):
    user = await _current_user(request)
    sid = user["steamid"]
    first_time = await db.users.find_one_and_update(
        {"steamid": sid, "welcomed": {"$ne": True}}, {"$set": {"welcomed": True}}
    )
    if first_time:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "steamid": sid, "read": False, "created_at": datetime.now(timezone.utc),
            "title": "Добро пожаловать на Steamgrader",
            "text": "Аккаунт Steam привязан. Общий чат уже открыт во вкладке «Сообщество».",
        })
    docs = await db.notifications.find({"steamid": sid}, {"_id": 0, "steamid": 0}).sort("created_at", -1).limit(20).to_list(20)
    for d in docs:
        d["created_at"] = d["created_at"].replace(tzinfo=timezone.utc).isoformat()
    unread = await db.notifications.count_documents({"steamid": sid, "read": False})
    return {"items": docs, "unread": unread}


@api_router.post("/notifications/read")
async def notifications_read(request: Request):
    user = await _current_user(request)
    await db.notifications.update_many({"steamid": user["steamid"], "read": False}, {"$set": {"read": True}})
    return {"ok": True}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def start_index_build():
    app.state.index_task = asyncio.create_task(ensure_indexes())  # background: a big index build must not block boot

@app.on_event("shutdown")
async def shutdown_db_client():
    app.state.index_task.cancel()  # stop a build still running before its client closes
    with suppress(asyncio.CancelledError):
        await app.state.index_task
    client.close()