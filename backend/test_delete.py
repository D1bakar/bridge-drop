"""Delete anything: file removed from disk + history rows gone."""

import db
from fastapi.testclient import TestClient

from app import UPLOAD_ROOT, app

client = TestClient(app)


def setup_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM transfers")
        conn.commit()


def teardown_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM transfers")
        conn.commit()


def test_delete_file_removes_disk_and_history():
    r = client.post("/v1/files", files={"file": ("gone.txt", b"bye")})
    assert r.status_code == 201
    assert (UPLOAD_ROOT / "gone.txt").exists()
    assert any(i["name"] == "gone.txt" for i in client.get("/v1/feed").json()["items"])
    d = client.delete("/v1/files/gone.txt")
    assert d.status_code == 200
    assert not (UPLOAD_ROOT / "gone.txt").exists()
    assert not any(i.get("name") == "gone.txt" for i in client.get("/v1/feed").json()["items"])
    assert client.delete("/v1/files/gone.txt").status_code == 404


def test_delete_file_guards():
    assert client.delete("/v1/files/.gitkeep").status_code == 404
    assert client.delete("/v1/files/..%2Fapp.py").status_code in (404, 422)
    assert client.delete("/v1/files/nope-nothing.txt").status_code == 404
    # staging files are never deletable / downloadable through this path
    (UPLOAD_ROOT / ".up-x.part").write_bytes(b"staging")
    try:
        assert client.delete("/v1/files/.up-x.part").status_code == 404
        assert client.get("/v1/files/.up-x.part").status_code == 404
    finally:
        (UPLOAD_ROOT / ".up-x.part").unlink(missing_ok=True)
