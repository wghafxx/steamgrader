"""Tests for Steam OpenID auth endpoints (no real Steam login attempted)."""
import os
import pytest
import requests
from urllib.parse import urlparse, parse_qs

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://steam-casino-home--9m03j9jj.preview.emergentagent.com").rstrip("/")
PUBLIC_BASE = BASE_URL  # frontend uses the same host; callback also lives here


@pytest.fixture
def client():
    s = requests.Session()
    return s


class TestAuthMe:
    def test_me_without_cookie_returns_null(self, client):
        r = client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert "user" in data
        assert data["user"] is None

    def test_me_with_invalid_cookie_returns_null(self, client):
        r = client.get(f"{BASE_URL}/api/auth/me", cookies={"session": "not-a-jwt"})
        assert r.status_code == 200
        assert r.json()["user"] is None


class TestSteamLoginRedirect:
    def test_steam_login_redirects_to_steamcommunity(self, client):
        r = client.get(f"{BASE_URL}/api/auth/steam", allow_redirects=False)
        assert r.status_code in (302, 303, 307), f"got {r.status_code}"
        loc = r.headers.get("location", "")
        assert "steamcommunity.com/openid/login" in loc, f"bad location: {loc}"

        parsed = urlparse(loc)
        qs = parse_qs(parsed.query)
        assert qs.get("openid.mode", [""])[0] == "checkid_setup"
        assert qs.get("openid.ns", [""])[0] == "http://specs.openid.net/auth/2.0"
        assert qs.get("openid.return_to", [""])[0] == f"{PUBLIC_BASE}/api/auth/steam/callback"
        # realm must be the public host (with trailing slash in impl)
        realm = qs.get("openid.realm", [""])[0]
        assert realm.startswith(PUBLIC_BASE), f"bad realm: {realm}"
        assert qs.get("openid.identity", [""])[0] == "http://specs.openid.net/auth/2.0/identifier_select"
        assert qs.get("openid.claimed_id", [""])[0] == "http://specs.openid.net/auth/2.0/identifier_select"


class TestSteamCallback:
    def test_callback_cancel_redirects_without_session(self, client):
        r = client.get(f"{BASE_URL}/api/auth/steam/callback", params={"openid.mode": "cancel"}, allow_redirects=False)
        assert r.status_code in (302, 303, 307)
        loc = r.headers.get("location", "")
        assert "login=cancelled" in loc
        # must NOT set session cookie
        set_cookie = r.headers.get("set-cookie", "") or ""
        assert "session=" not in set_cookie or "session=;" in set_cookie.lower()

    def test_callback_missing_mode_treated_as_cancel(self, client):
        r = client.get(f"{BASE_URL}/api/auth/steam/callback", allow_redirects=False)
        assert r.status_code in (302, 303, 307)
        assert "login=cancelled" in r.headers.get("location", "")

    def test_callback_invalid_assertion_rejected(self, client):
        # id_res with fake data -> Steam check_authentication returns is_valid:false -> 401
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "id_res",
            "openid.op_endpoint": "https://steamcommunity.com/openid/login",
            "openid.claimed_id": "https://steamcommunity.com/openid/id/76561198000000000",
            "openid.identity": "https://steamcommunity.com/openid/id/76561198000000000",
            "openid.return_to": f"{PUBLIC_BASE}/api/auth/steam/callback",
            "openid.response_nonce": "2026-01-01T00:00:00Zfake",
            "openid.assoc_handle": "fake",
            "openid.signed": "signed,op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle",
            "openid.sig": "ZmFrZXNpZ25hdHVyZQ==",
        }
        r = client.get(f"{BASE_URL}/api/auth/steam/callback", params=params, allow_redirects=False)
        # must NOT set session cookie
        set_cookie = r.headers.get("set-cookie", "") or ""
        assert "session=" not in set_cookie or "session=;" in set_cookie.lower()
        # Expected 303 redirect to /?login=failed per impl (verification failed)
        assert r.status_code in (302, 303, 307), f"unexpected status {r.status_code}: {r.text[:200]}"
        assert "login=failed" in r.headers.get("location", "")

    def test_callback_bad_return_to_rejected(self, client):
        params = {
            "openid.mode": "id_res",
            "openid.claimed_id": "https://steamcommunity.com/openid/id/76561198000000000",
            "openid.return_to": "https://evil.example/callback",
        }
        r = client.get(f"{BASE_URL}/api/auth/steam/callback", params=params, allow_redirects=False)
        assert r.status_code == 400


class TestLogout:
    def test_logout_clears_cookie(self, client):
        r = client.post(f"{BASE_URL}/api/auth/logout")
        assert r.status_code == 200
        assert r.json().get("ok") is True
        set_cookie = (r.headers.get("set-cookie") or "").lower()
        # delete_cookie emits Max-Age=0 or expires in past
        assert "session=" in set_cookie
        assert ("max-age=0" in set_cookie) or ("expires=" in set_cookie)
