"""Mobile row alignment: text sits on baseline inside every box (Home/History/Pair/Send/Settings)."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_side_cluster_is_flex_centered():
    home = client.get("/css/home.css").text
    assert ".recent-side" in home
    # flex row, vertically centered, wraps instead of squeezing text
    assert "display: flex" in home
    assert "align-items: center" in home
    assert "flex-wrap: wrap" in home


def test_row_links_have_no_top_margin():
    home = client.get("/css/home.css").text
    assert ".recent-side .action-secondary" in home
    assert "margin-top: 0" in home


def test_pair_trusted_uses_side_wrapper():
    js = client.get("/js/pair-page.js").text
    assert "recent-side" in js


def test_batch_and_settings_rows_wrap():
    pages = client.get("/css/pages.css").text
    assert ".batch-row" in pages
    assert ".settings-row" in pages
    assert "flex-wrap: wrap" in pages
    assert "min-width: 0" in pages
