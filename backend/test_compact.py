"""Home compact (phone only): capped preview, tight fold, one-line composer."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_recent_preview_capped():
    js = client.get("/js/mock.js").text
    assert "slice(0, 3)" in js
    assert "history.html" in js


def test_phone_fold_compact():
    home = client.get("/css/home.css").text
    assert "min-height: 120px" in home
    assert "--section-gap: 24px" in home
    assert ".snippet-form .field-area" in home
    assert 'rows="1"' in client.get("/").text


def test_action_margin_compact():
    apple = client.get("/css/apple.css").text
    assert ".action-primary" in apple
