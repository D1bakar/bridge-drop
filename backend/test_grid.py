"""Text grid: token rhythm, inset codes, locked 34px large title."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_meta_and_section_rhythm():
    home_css = client.get("/css/home.css").text
    assert "p.recent-meta" in home_css
    pages_css = client.get("/css/pages.css").text
    assert "main > section:not([class])" in pages_css
    assert "#claim-block .pair-code" in pages_css


def test_large_title_locked():
    apple = client.get("/css/apple.css").text
    assert ".page-heading" in apple
    pages = client.get("/css/pages.css").text
    assert "clamp(40px, 13vw, 64px)" not in pages
