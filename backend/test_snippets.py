"""Snippets: post text/link, auto-detect links, list, feed search, delete."""

import db
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def setup_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM snippets")
        conn.commit()


def teardown_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM snippets")
        conn.commit()


def test_post_and_list_snippets():
    r = client.post("/v1/snippets", json={"body": "hello bridge"})
    assert r.status_code == 201
    assert r.json()["kind"] == "text"
    r2 = client.post("/v1/snippets", json={"body": "https://example.com/x"})
    assert r2.json()["kind"] == "link"
    items = client.get("/v1/snippets").json()["snippets"]
    assert len(items) == 2
    assert items[0]["body"] == "https://example.com/x"  # newest first


def test_empty_and_oversize_rejected():
    assert client.post("/v1/snippets", json={"body": "  "}).status_code == 422
    assert client.post("/v1/snippets", json={"body": "x" * 100_001}).status_code == 413


def test_feed_search_finds_snippet_and_delete():
    sid = client.post("/v1/snippets", json={"body": "unique-token-abc-123"}).json()["id"]
    found = client.get("/v1/feed", params={"q": "unique-token-abc"}).json()["items"]
    assert any(i["type"] == "snippet" and i["id"] == sid for i in found)
    assert client.delete(f"/v1/feed/snippet/{sid}").status_code == 200
    assert client.delete(f"/v1/feed/snippet/{sid}").status_code == 404
    assert not any(i["id"] == sid for i in client.get("/v1/feed").json()["items"])
