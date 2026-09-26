"""HIG layout pass: 16pt compact edge, 16pt card padding, scaling guard."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_compact_edge_16pt():
    css = client.get("/css/tokens.css").text
    assert "--edge: 16px" in css
    assert "--edge: 40px" in css  # desktop source-style edge kept


def test_card_padding_tokenized():
    home = client.get("/css/home.css").text
    assert "--surface-pad: 16px" in home
    pages = client.get("/css/pages.css").text
    assert "padding: 20px" not in pages
    assert "text-size-adjust: 100%" in home
