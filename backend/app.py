"""Bridge M0 backend skeleton — PRD §9 contract starts here.

Run: uvicorn app:app --reload --port 8000  (from backend/)
Contract (frontend untouched, still on mock.js):
  GET /v1/info — device info + capabilities
"""

from fastapi import FastAPI

app = FastAPI(title="Bridge M0")


@app.get("/")
def root():
    return {"ok": True, "service": "bridge-m0"}
