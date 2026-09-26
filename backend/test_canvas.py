"""Transfer canvas: spatial hooks, page drag mode, journey wiring."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_home_canvas_hooks():
    html = client.get("/").text
    assert 'id="dropzone"' in html
    assert "bridge-mark" in html
    assert 'id="dest-name"' in html
    assert 'id="net-status"' in html
    assert html.count('id="net-status"') == 1
    assert 'class="glyph"' not in html


def test_page_drag_and_journey_wired():
    dz = client.get("/js/dropzone.js").text
    assert "is-dragging" in dz
    up = client.get("/js/upload.js").text
    assert "setTx" in up
    assert "--tx" in up
    assert "is-done" in up
    assert "is-transferring" in up
    css = client.get("/css/home.css").text
    assert ".bridge-pulse" in css
    assert ".field.is-dragover" in css
    assert "body.is-dragging" in css


def test_pair_flow_and_direction():
    pair = client.get("/pair.html").text
    assert "This device" in pair
    assert "New phone" in pair
    assert "flow-end" in client.get("/css/pages.css").text
    feed = client.get("/js/feed.js").text
    assert "dataset.dir" in feed
    assert "dataset.dir" in client.get("/js/mock.js").text
    assert '[data-dir="in"]' in client.get("/css/home.css").text
