"""Tests for notifications endpoints (GET/POST /api/notifications*)."""
import os
import uuid
import pytest
import requests
from datetime import datetime, timezone
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


def _read_session(path):
    try:
        return open(path).read().strip()
    except Exception:
        return None


SESSION1 = _read_session("/tmp/test_session_1")


@pytest.fixture
def anon():
    s = requests.Session()
    return s


@pytest.fixture
def user1():
    if not SESSION1:
        pytest.skip("No /tmp/test_session_1")
    s = requests.Session()
    s.cookies.set("session", SESSION1)
    return s


# --- Auth guard ---

def test_notifications_get_unauth(anon):
    r = anon.get(f"{API}/notifications")
    assert r.status_code == 401


def test_notifications_read_unauth(anon):
    r = anon.post(f"{API}/notifications/read")
    assert r.status_code == 401


# --- Logged-in flows ---

def test_notifications_list_shape_and_welcome(user1):
    r = user1.get(f"{API}/notifications")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data and "unread" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["unread"], int)
    # Welcome notification should exist
    titles = [i.get("title") for i in data["items"]]
    assert any("Steamgrader" in (t or "") or "Добро пожаловать" in (t or "") for t in titles)
    for it in data["items"]:
        assert "steamid" not in it
        assert "_id" not in it
        assert "title" in it and "text" in it and "created_at" in it
        assert "read" in it


def test_welcome_not_duplicated(user1):
    r1 = user1.get(f"{API}/notifications").json()
    r2 = user1.get(f"{API}/notifications").json()
    n1 = sum(1 for i in r1["items"] if "Добро пожаловать" in (i.get("title") or ""))
    n2 = sum(1 for i in r2["items"] if "Добро пожаловать" in (i.get("title") or ""))
    assert n1 == n2 == 1


def test_read_marks_unread_zero(user1):
    # Insert a direct unread doc via API seeding not possible without db access; use motor
    pass


# --- DB-driven assertions: unread badge toggles, cross-user isolation ---

@pytest.fixture
def db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    client = MongoClient(mongo_url)
    yield client[db_name]
    client.close()


def test_unread_increments_then_clears(user1, db):
    doc_id = str(uuid.uuid4())
    db.notifications.insert_one({
        "id": doc_id, "steamid": "1", "read": False,
        "created_at": datetime.now(timezone.utc),
        "title": "TEST_notification", "text": "TEST_body",
    })
    try:
        r = user1.get(f"{API}/notifications").json()
        assert r["unread"] >= 1
        ids = [i.get("id") for i in r["items"]]
        assert doc_id in ids
        ok = user1.post(f"{API}/notifications/read")
        assert ok.status_code == 200
        r2 = user1.get(f"{API}/notifications").json()
        assert r2["unread"] == 0
    finally:
        db.notifications.delete_one({"id": doc_id})


def test_cross_user_isolation(user1, db):
    doc_id = str(uuid.uuid4())
    db.notifications.insert_one({
        "id": doc_id, "steamid": "9999999999", "read": False,
        "created_at": datetime.now(timezone.utc),
        "title": "TEST_other_user", "text": "TEST",
    })
    try:
        r = user1.get(f"{API}/notifications").json()
        ids = [i.get("id") for i in r["items"]]
        assert doc_id not in ids
    finally:
        db.notifications.delete_one({"id": doc_id})
