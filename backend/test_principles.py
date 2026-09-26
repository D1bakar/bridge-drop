"""HIG principles: persistent failure feedback, forgiving deletes, live progress."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_failure_toasts_sticky():
    api = client.get("/js/api.js").text
    assert "opts.sticky" in api
    assert client.get("/js/feed.js").text.count("{ sticky: true }") >= 5
    assert client.get("/js/mock.js").text.count("{ sticky: true }") >= 3


def test_delete_asks_twice():
    assert "confirmDelete" in client.get("/js/feed.js").text
    assert "confirmDelete" in client.get("/js/mock.js").text
    assert "Sure?" in client.get("/js/feed.js").text


def test_progress_announced():
    assert 'aria-live="polite"' in client.get("/").text
    assert 'aria-live="polite"' in client.get("/send.html").text
