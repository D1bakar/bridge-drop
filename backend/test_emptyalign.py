"""Empty states sit in the same 16px text column as rows — no edge touch, no double border."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_empty_shares_row_inset():
    home = client.get("/css/home.css").text
    assert ".recent-empty" in home
    assert "margin: 0 15px" in home
    assert ".recent-empty .action-secondary" in home
    assert "margin-top: 0" in home


def test_empty_in_grouped_cards():
    apple = client.get("/css/apple.css").text
    assert ".recent-empty" in apple
