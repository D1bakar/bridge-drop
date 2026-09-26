"""Liquid Glass system: functional glass, matte content, honest motion."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_material_tokens_centralized():
    css = client.get("/css/apple.css").text
    assert "--ease-spring" in css
    assert "--z-toast" in css
    assert "--glass-clear-alpha" in css
    assert "z-index: var(--z-nav)" in css


def test_content_matte_nav_glass():
    css = client.get("/css/apple.css").text
    assert "box-shadow: none" in css
    assert "backdrop-filter: blur(var(--glass-blur))" in css


def test_scroll_edge_and_motion():
    css = client.get("/css/apple.css").text
    assert ".tabbar.is-scrolled" in css
    assert "var(--ease-spring)" in css
    assert "var(--motion-fast)" in css
    assert "is-scrolled" in client.get("/js/tabbar.js").text


def test_reduced_transparency():
    css = client.get("/css/apple.css").text
    assert "prefers-reduced-transparency" in css
    assert "prefers-reduced-transparency" in client.get("/js/clarity.js").text
