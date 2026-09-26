"""Redesign system: new token foundation ships with the shell."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_redesign_tokens_present():
    css = client.get("/css/tokens.css").text
    for tok in ("--type-ltitle", "--type-body", "--type-foot", "--type-cap",
                "--type-t3",
                "--font-system", "--r-sm", "--r-md", "--r-lg", "--r-xl",
                "--space-half", "--space-4", "--z-content", "--z-func",
                "--z-sheet", "--motion-slow"):
        assert tok in css, tok


def test_ramp_adopted_not_decorative():
    home = client.get("/css/home.css").text
    assert "var(--type-body)" in home
    assert "var(--type-t2)" in home
    assert "var(--type-t3)" in home
    pages = client.get("/css/pages.css").text
    assert "var(--type-body)" in pages
    assert "var(--type-foot)" in pages


def test_dock_owns_navigation():
    apple = client.get("/css/apple.css").text.replace("\r\n", "\n")
    assert ".topnav {\n  display: none;" in apple
    assert ".tabbar {\n  display: flex;" in apple
    assert "translateX(-50%)" in apple


def test_motion_explains_state():
    pages = client.get("/css/pages.css").text
    assert "toast-in" in pages
    assert "prefers-reduced-motion: no-preference" in pages
    assert "transition: width 150ms linear" in pages


def test_atmosphere_and_desktop():
    home = client.get("/css/home.css").text
    assert "radial-gradient" in home
    assert "min-width: 1200px" in home
    assert "max-width: 760px" in home


def test_dock_focus_visible():
    apple = client.get("/css/apple.css").text
    assert ".tabbar a:focus-visible" in apple
