# bridge-drop

Instant PC ↔ Phone transfer — LAN-first, original quality, no cable, no cloud, no chat app in the middle.

Drop anything on one device, it appears on the other in seconds. One persistent
feed for files, text, and links. Phone needs no install — just the browser.

## Status

Working product (web-mode, PRD M0 + web-applicable P0/P1): multi-file and folder
uploads with resume, text/link snippets, persistent searchable history, QR pairing
with trusted devices, save rules, settings. See `prd.md` for roadmap, `design.md`
for the design system.

## Run — one terminal

Double-click **`start-bridge.bat`**, or from `backend/`:

```powershell
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Startup prints `PC: http://127.0.0.1:8000/` + `Phone (same Wi-Fi): http://<LAN-IP>:8000/`.
Open the first on the PC, the second on the phone (same Wi-Fi). Keep the window open.

Windows note: if the phone can't reach the PC, set Wi-Fi to Private
(Settings → Network) and allow Python on the firewall prompt. Public profile
blocks inbound (prd §11).

## Everyday flows

- **Phone → PC (no install):** PC opens `Pair` → phone camera scans the QR →
  phone taps Pair → phone `Send` page uploads photos/videos (multi-select or whole
  folder) with progress, speed, ETA, cancel. Files land in `backend/uploads/`.
- **PC → phone:** drag files onto `Send`, or pick a folder. On the phone, open
  `History` and tap any file to download it at original quality.
- **Text / links:** type in `Share text` on Home → appears
  in the feed on both ends → `Copy →` pastes anywhere (covers clipboard push, U7).
- **Guest / iPhone:** same QR flow in any mobile browser, nothing to install (W3).
- **History:** every file + snippet, newest first, searchable. Delete rows; delete
  with file removal from the row action on Home preview. Re-download anytime.
- **Interruptions:** uploads resume from confirmed bytes (check `Send` again after
  a drop — completed chunks are kept). Hashes verified on finalize; mismatches
  rejected, never stored.
- **Strangers:** guests need a live 5-minute code. With auto-accept OFF (Settings),
  guest files wait in History as `Waiting — Accept → / Decline →`.

## Pages

- `/` Home — drop prompt, quick dropzone, devices, share-text, recent preview
- `/send.html` — batch + folder sender with per-file progress and cancel
- `/history.html` — full searchable feed (files + snippets)
- `/pair.html` — QR + short code, claim, trusted devices (rename, revoke)
- `/settings.html` — device name, auto-accept, visibility, save rules (`ext → folder`)

## API (PRD §9)

| Endpoint | Purpose |
|---|---|
| `GET /v1/info` | Device info + capabilities |
| `GET /v1/files` · `GET /v1/files/{path}` | List (recursive) · download/open |
| `POST /v1/files` | Simple multipart upload (+`relPath`) |
| `POST /v1/uploads/init` · `PUT /v1/uploads/{id}/chunk?offset=` · `GET …/status` · `POST …/complete` · `DELETE …` | Chunked resumable upload, hash verify, cancel |
| `POST /v1/snippets` · `GET /v1/snippets` | Text/link/clipboard store + list |
| `GET /v1/feed` (`?q=`, `?kind=`) | Persistent history, searchable |
| `DELETE /v1/feed/file/{id}` (`?delete_file=1`) · `DELETE /v1/feed/snippet/{id}` | Delete rows |
| `POST /v1/feed/accept/{id}` · `POST /v1/feed/decline/{id}` | Accept/decline waiting guests |
| `POST /v1/pair/code` · `GET /v1/pair/qr` · `POST /v1/pair/claim` | One-time code, QR art, claim |
| `GET /v1/devices` · `PATCH /v1/devices/{id}` · `DELETE /v1/devices/{id}` | Trusted list, rename, revoke |
| `GET/PATCH /v1/settings` · `GET/POST/DELETE /v1/rules` | Prefs + save rules |

Data: `backend/bridge.db` (SQLite, gitignored) + `backend/uploads/`. No accounts,
no telemetry, nothing leaves the LAN.

## Project layout

- `index.html`, `send.html`, `history.html`, `pair.html`, `settings.html` — screens
- `css/tokens.css` — design tokens (`design.md` §12, verbatim, do not edit)
- `css/home.css`, `css/pages.css` — page styles
- `js/api.js` — base resolution, device token, toast (shared)
- `js/mock.js` — Home devices + recent preview (server, mock fallback)
- `js/dropzone.js`, `js/upload.js` — Home quick dropzone + single upload
- `js/batch.js` — Send page chunked batch engine
- `js/feed.js` — history feed, search, snippets, accept/decline
- `js/pair-page.js`, `js/settings-page.js` — Pair + Settings screens
- `backend/app.py`, `backend/db.py` — API + storage
- `backend/test_*.py` — suite (`python -m pytest backend -q`)

## Honest scope (what this build is not)

Per `prd.md` phases, native-app territory stays out: no mDNS discovery in-browser
(use QR / manual URL), no Android share-sheet / tray / context-menu / hotkey (needs
the M1 native app), no off-LAN relay or WebRTC (M4), no mutual-TLS (LAN HTTP +
one-time codes + trusted-device tokens; enable OS firewall + Private profile).
Dark theme deferred per `design.md`.

## Git flow

`main` always runnable. Work on `feat/*` branches, micro-commits, PR → merge →
`git pull`.
