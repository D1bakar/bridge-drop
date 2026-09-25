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

## Run (M0 LAN — phone browser to PC)

Terminal 1 — backend (from `backend/`):

```powershell
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Startup prints `PC: http://127.0.0.1:8000/v1/info` + `Phone (same Wi-Fi): http://<LAN-IP>:8000/v1/info`.

Terminal 2 — frontend:

Open `index.html` via VS Code Live Server (port 5500). No build step.

Phone test (same Wi-Fi): open `http://<LAN-IP>:5500` → Choose files → file lands in `backend/uploads/` → Recent feed shows it with `Live` pill.

Windows note: if the phone can't reach the PC, set Wi-Fi to Private (Settings → Network) and allow Python on the firewall prompt. Public profile blocks inbound (prd §11).

## Git flow

`main` always runnable. Work on `feat/*` / `chore/*` branches, micro-commits, PR → merge → `git pull`.
