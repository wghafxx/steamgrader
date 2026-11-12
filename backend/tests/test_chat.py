"""Backend tests for community chat endpoints (/api/chat/messages)."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://steam-casino-home--9m03j9jj.preview.emergentagent.com").rstrip("/")


def _read_session(path):
    with open(path) as f:
        return f.read().strip()


@pytest.fixture(scope="module")
def session1():
    s = requests.Session()
    s.cookies.set("session", _read_session("/tmp/test_session_1"))
    return s


@pytest.fixture(scope="module")
def session2():
    s = requests.Session()
    s.cookies.set("session", _read_session("/tmp/test_session_2"))
    return s


# ---- Auth guard ----
class TestAuthGuard:
    def test_get_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/chat/messages")
        assert r.status_code == 401

    def test_post_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/chat/messages", json={"text": "hi"})
        assert r.status_code == 401


# ---- Chat listing ----
class TestChatList:
    def test_list_returns_messages(self, session1):
        r = session1.get(f"{BASE_URL}/api/chat/messages")
        assert r.status_code == 200
        data = r.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)


# ---- Send message & validations ----
class TestSendMessage:
    def test_send_plain_message(self, session1):
        time.sleep(3.2)
        text = f"TEST_msg_{int(time.time())}"
        r = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": text})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["text"] == text
        assert d["steamid"] == "1"
        assert "created_at" in d and "id" in d

        # GET verifies persistence
        time.sleep(0.3)
        lst = session1.get(f"{BASE_URL}/api/chat/messages").json()["messages"]
        assert any(m["id"] == d["id"] for m in lst)

    @pytest.mark.parametrize("link", [
        "смотри http://example.com",
        "zайди www.example.com",
        "t.me/somechan",
        "join discord.gg/abc",
        "site . ru сайт",
    ])
    def test_links_rejected(self, session1, link):
        time.sleep(3.2)
        r = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": link})
        assert r.status_code == 400
        assert "Ссылки" in r.json().get("detail", "")

    def test_cooldown_429(self, session1):
        time.sleep(3.2)
        session1.post(f"{BASE_URL}/api/chat/messages", json={"text": f"TEST_cool_{int(time.time())}"})
        r = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": f"TEST_cool2_{int(time.time())}"})
        assert r.status_code == 429

    def test_duplicate_within_60s_rejected(self, session1):
        time.sleep(3.2)
        text = f"TEST_dup_{int(time.time())}"
        r1 = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": text})
        assert r1.status_code == 200
        time.sleep(3.2)
        r2 = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": text})
        assert r2.status_code == 400

    def test_repeat_chars_rejected(self, session1):
        time.sleep(3.2)
        r = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": "aaaaaaaaaaaa"})
        assert r.status_code == 400

    def test_over_300_chars_rejected(self, session1):
        time.sleep(3.2)
        r = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": "a" + "b" * 310})
        assert r.status_code == 422

    def test_html_stored_as_text(self, session1):
        time.sleep(3.2)
        text = f"<script>alert({int(time.time())})</script>"
        r = session1.post(f"{BASE_URL}/api/chat/messages", json={"text": text})
        # text is harmless literal - should pass (no link, no repeat), 
        # though tag words can contain 'script' - should still be ok
        assert r.status_code == 200, r.text
        assert r.json()["text"] == text


# ---- Cross-user visibility ----
class TestCrossUser:
    def test_user2_message_visible_to_user1(self, session1, session2):
        time.sleep(3.2)
        text = f"TEST_fromU2_{int(time.time())}"
        r = session2.post(f"{BASE_URL}/api/chat/messages", json={"text": text})
        assert r.status_code == 200, r.text
        time.sleep(0.5)
        msgs = session1.get(f"{BASE_URL}/api/chat/messages").json()["messages"]
        assert any(m["text"] == text and m["steamid"] == "2" for m in msgs)
