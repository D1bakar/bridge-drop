# bridge-drop

Instant PC ↔ Phone transfer — LAN-first, original quality, no cable, no cloud, no chat app in the middle.

Drop anything on one device, it appears on the other in seconds.

## Status

M0 prototype (in progress): Python + plain HTML/CSS/JS web-mode. See `prd.md` for roadmap, `design.md` for design system.

## Docs

- `prd.md` — PRD v0.1: Bridge — Instant PC ↔ Phone Transfer
- `design.md` — Design System: Monumental type on warm concrete (light-only v1)

## Frontend (M0 web-mode)

- `index.html` — Home shell
- `css/tokens.css` — Design tokens (`design.md` §12, verbatim)
- `css/home.css` — Home page styles
- `js/mock.js` — Mock devices (frontend-only, no backend calls yet)

Backend contract (do not touch from frontend): `GET /v1/info`, `POST /v1/session` per `prd.md` §9.

## Run (M0 — one terminal, no Live Server needed)

From `backend/`:

```powershell
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Startup prints `PC: http://127.0.0.1:8000/` + `Phone (same Wi-Fi): http://<LAN-IP>:8000/`.

Open that URL on PC and on the phone (same Wi-Fi) → Choose files → file lands in `backend/uploads/` → Recent feed shows it with `Live` pill. Same origin, so no CORS/host guessing.

Alt (dev): open `index.html` via VS Code Live Server (`:5500`) — page still talks to `:8000` via fallback candidates.

Windows note: if the phone can't reach the PC, set Wi-Fi to Private (Settings → Network) and allow Python on the firewall prompt. Public profile blocks inbound (prd §11).

## Git flow

`main` always runnable. Work on `feat/*` / `chore/*` branches, micro-commits, PR → merge → `git pull`.
