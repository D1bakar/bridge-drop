"""Redesign system: new token foundation ships with the shell."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_redesign_tokens_present():
    css = client.get("/css/tokens.css").text
    for tok in ("--type-ltitle", "--type-body", "--type-foot", "--type-cap",
                "--font-system", "--r-sm", "--r-md", "--r-lg", "--r-xl",
                "--space-half", "--space-4", "--z-content", "--z-func",
                "--z-sheet", "--motion-slow"):
        assert tok in css, tok
