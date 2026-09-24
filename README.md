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

## Run

Open `index.html` via VS Code Live Server. No build step.

## Git flow

`main` always runnable. Work on `feat/*` / `chore/*` branches, micro-commits, PR → merge → `git pull`.
