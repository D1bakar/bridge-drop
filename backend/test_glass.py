"""Ultra-clear Liquid Glass: low floor, light-bend layers, readable labels."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_clarity_default_and_floor():
    js = client.get("/js/clarity.js").text
    assert "var DEFAULT = 8" in js
    assert "0.16" in js
    assert 'value="8"' in client.get("/settings.html").text


def test_css_fallback_clear_light_pill():
    css = client.get("/css/apple.css").text
    assert "--glass-alpha: 0.22" in css
    assert css.count("background: rgba(38, 37, 35, 0.05)") == 2


def test_liquid_light_bend_mono():
    css = client.get("/css/apple.css").text
    assert "linear-gradient(180deg" in css
    assert "brightness(1.06)" in css
    assert "text-shadow" in css
