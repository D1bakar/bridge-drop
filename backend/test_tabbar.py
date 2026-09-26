"""Tab glide regression: pill parks instantly, no scale pop (design.md S7)."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_tabbar_first_paint_no_anim():
    js = client.get("/js/tabbar.js").text
    assert "ind.style.transition = 'none'" in js
    assert "requestAnimationFrame" in js


def test_tabbar_repin_and_motion():
    js = client.get("/js/tabbar.js").text
    assert "document.fonts" in js
    assert "prefers-reduced-motion" in js
    assert "e.ctrlKey" in js and "e.metaKey" in js


def test_tab_pill_200ms_no_scale():
    css = client.get("/css/apple.css").text
    assert "scale(0.88)" not in css
    assert "left var(--duration)" in css
