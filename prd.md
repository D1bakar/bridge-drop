PRD: Bridge — Instant PC ↔ Phone Transfer
Working title: Bridge (rename later) · Version: 0.1 · Date: 24 Sep 2026 · Owner: Solo founder/dev · Status: Draft for validation

0. Reality check (read this first)
This problem is already solved by free tools. Verify current feature sets before you lock scope, but as of now:

Tool	What it does	Where it's weak
LocalSend	Free, open-source, encrypted, LAN-only sharing across Windows, macOS, Linux, Android, iOS	LAN only. No persistent feed. No off-network path
KDE Connect	Files + clipboard sync, works on Windows and Android	Broader "phone integration" suite, heavier, iOS support limited
PairDrop / Snapdrop	Browser-based, WebRTC, no install	Needs both devices online in a browser, no history, no background receive
Phone Link (Microsoft)	Windows ↔ phone integration	Tied to Microsoft ecosystem, file transfer is a side feature
Syncthing / Taildrop	Folder sync / tailnet file send	Setup-heavy, not a "just send this" flow
If your only goal is "stop using WhatsApp for this," install LocalSend today. Ten minutes. Done.

Build Bridge only if at least one of these is true:

It's a learning + portfolio project (legit, and this PRD is written to serve that).
You're going after a wedge the incumbents don't cover:
W1 – One persistent feed (files, text, links, clipboard) that is instant on the LAN and reachable off the LAN. WhatsApp "message yourself" wins today because it has history and works anywhere. LAN-only tools lose there.
W2 – Media-creator workflow: multi-GB video exports, RAW photo batches, original quality, folder structure preserved, rules like "videos land in my project inbox folder."
W3 – Zero-install on one side: scan a QR, transfer from any phone browser (covers iPhone before a native iOS app exists).
This PRD targets W1 + W2 + W3, in phases, with a weekend prototype as a kill/continue gate (Section 13).

1. Overview
One-liner: Drop anything on one device, it appears on the other in seconds, at full quality, with no cable, no account fuss, and no chat app in the middle.

Problem: Moving a file, photo, link, or text between PC and phone currently means opening WhatsApp (or email, or a cable). It's slow to reach, compresses media, clutters chats, has size limits, and forces a chat UI onto a file-transfer job.

Vision: A tiny always-ready utility on both devices. Two actions: send and receive. Everything else stays out of the way.

2. Goals, non-goals, success metrics
Goals
G1: Phone → PC and PC → phone transfer in ≤ 3 taps/actions from anywhere in the OS.
G2: Original quality, any size (multi-GB video included), no compression.
G3: Fast on the LAN (direct device-to-device, no cloud hop).
G4: Secure by default — nothing lands on your device from a stranger.
G5: Works without internet on a shared Wi-Fi; optional fallback when not on the same network.
Non-goals (v1)
Not a chat app. Not a cloud drive. Not backup/sync of whole folders.
Not screen mirroring, notifications mirroring, or calls (that's Phone Link/KDE Connect territory).
No accounts, no ads, no analytics/telemetry in v1.
No macOS/Linux/iOS native apps in v1 (web-mode covers iPhone).
Success metrics
Metric	Target
First-time pairing	< 60 s from install
Paired device → first byte moving	< 5 s
Throughput on same Wi-Fi	≥ 70% of measured link speed; 1 GB in < 30 s on decent 5 GHz Wi-Fi
Transfer success rate (stable LAN)	≥ 99%
Actions to send (phone gallery → PC)	≤ 3 taps
Personal dogfood test	Zero WhatsApp file transfers for 14 consecutive days
3. Users & use cases
Primary user: a creator/power user who moves media between phone and PC daily — photos, RAW, screen recordings, video exports, reference clips, documents, links.

Secondary: students, freelancers, anyone tired of "WhatsApp to self."

#	User story	Priority
U1	As a user, I share a photo/video from my phone gallery to my PC without it being compressed.	P0
U2	As a user, I drag a file onto the PC app and it appears on my phone.	P0
U3	As a user, I send 30 files or a whole folder in one go and watch progress.	P0
U4	As a user, I send a link or text snippet to the other device.	P0
U5	As a user, an interrupted transfer resumes instead of restarting.	P0
U6	As a user, I see a history of what I've sent/received and can re-send.	P0
U7	As a user, I copy text on PC and paste it on my phone.	P1
U8	As a user, incoming videos auto-file into a folder I choose.	P1
U9	As a user on an iPhone or a friend's phone, I transfer via browser with no install.	P1
U10	As a user, I send from a different network (office, mobile data) end-to-end encrypted.	P2
4. Scope by phase
Phase	Platforms	Contents
M0 Prototype	PC (Python) + any phone browser	QR → web page, upload/download, paste text. Purpose: prove daily use
M1 MVP	Windows + Android (native)	Discovery, QR pairing, send/receive files + text, share sheet, progress, tray app
M2 Solid	Same	Resume, integrity check, history, folders, save rules, Explorer context menu, installer
M3 Wedge	Same + web mode	Clipboard sync, global hotkey/paste-to-send, web-mode for iPhone/guests
M4 Reach	+ iOS, + internet fallback	WebRTC/relay fallback, iOS app
5. Functional requirements
Priority: P0 = MVP · P1 = next · P2 = later.

A. Discovery & pairing
ID	Requirement	P
FR-1	Auto-discover devices on the same network (mDNS) and list them with name + platform	P0
FR-2	Pair by scanning a QR code shown on the PC (contains device ID, address, cert fingerprint, one-time token). No account	P0
FR-3	Trusted-devices list with rename and revoke	P0
FR-4	Manual connect by IP/code when mDNS is blocked	P1
FR-5	Hotspot mode (phone hotspot ↔ PC) when there is no shared Wi-Fi	P2
B. Sending
ID	Requirement	P
FR-6	PC: drag-and-drop onto window/tray, "Send files" button, paste (Ctrl+V)	P0
FR-7	Phone: appear in the Android Share Sheet; in-app picker for photos, videos, files	P0
FR-8	Multi-file selection in one batch	P0
FR-9	Folder send with structure preserved	P1
FR-10	Send text/links as snippets	P0
FR-11	PC Explorer right-click → "Send to phone"	P1
FR-12	Global hotkey on PC to send current clipboard/selection	P2
C. Receiving
ID	Requirement	P
FR-13	Trusted devices: auto-accept (toggleable). Unknown devices: explicit accept/deny prompt	P0
FR-14	Default save locations: PC Downloads\Bridge\; phone Downloads/Bridge (photos/videos also indexed into gallery)	P0
FR-15	Notification on receive with Open / Show in folder	P0
FR-16	Save rules by file type/source (e.g., video → D:\Projects\Inbox)	P1
D. Transfer engine
ID	Requirement	P
FR-17	Progress, speed, ETA; cancel per file and per batch	P0
FR-18	Streaming I/O — never load a whole file into RAM. Files > 4 GB supported	P0
FR-19	Original bytes only: no recompression, filename + modified time preserved, EXIF intact	P0
FR-20	Integrity verification (hash) after transfer; auto-retry on mismatch	P1
FR-21	Resume from last confirmed chunk after network drop or app kill	P0
FR-22	Queue with pause/resume; limited parallelism	P1
E. History / feed
ID	Requirement	P
FR-23	Chronological feed of transfers and snippets with status; tap to open, re-send, delete	P0
FR-24	Search history	P1
FR-25	Auto-clear rules (older than N days)	P2
F. Clipboard & web mode
ID	Requirement	P
FR-26	Manual clipboard push ("Send clipboard")	P1
FR-27	Opt-in automatic clipboard sync between paired devices	P2
FR-28	Web mode: PC shows a QR; any phone browser opens a local page to upload to / download from the PC (HTTPS, one-time code, auto-expires)	P1
G. Off-network fallback
ID	Requirement	P
FR-29	When peers aren't on the same LAN, connect via WebRTC (signaling server + TURN relay); end-to-end encrypted; server never sees content	P2
H. Settings & app shell
ID	Requirement	P
FR-30	Device name, save folder, auto-accept, visibility (Visible / Hidden), start with Windows	P0
FR-31	PC: system tray app, single instance, minimize to tray	P0
FR-32	Dark/light theme following OS	P1
6. Key user flows
Pairing (once): Install on both → PC opens, shows QR → phone taps Pair, scans → both show the peer's name + a short fingerprint to confirm → paired. Target: under 60 s.

Phone → PC: Gallery → select photos/videos → Share → Bridge → tap the PC → progress notification → PC toast "5 files received — Show in folder."

PC → Phone: Drag file(s) onto the tray/window (or Ctrl+V) → pick the phone (or it's auto-selected if only one is paired) → phone notification → files land in Downloads/Bridge (media appears in gallery).

Guest / iPhone (web mode): PC → Share via browser → QR → phone camera opens the page → pick files → uploaded to PC.

Off-network (P2): Same flows; the app shows a "Relay" badge and reduces speed expectations.

Screens (MVP): Home (devices + drop zone), Transfer progress, History/feed, Pair, Settings, Incoming-request dialog.

7. Non-functional requirements
Area	Requirement
Performance	≥ 70% of link throughput; UI stays responsive during multi-GB transfers
Reliability	Resume after drops; no corrupt files (hash-verified); no partial files left in the destination folder (write to .part, rename on success)
Battery (phone)	No constant background listening. Receive while app is open or via a foreground service during an active transfer
Resources (PC)	Idle < 1% CPU; memory footprint target < 150 MB
Offline	Full functionality on LAN with zero internet
Privacy	No telemetry; LAN path never touches any server; local logs only
Security	TLS 1.3, mutual authentication, pinned certificates (Section 10)
Compatibility	Windows 10/11; Android 10+ (adjust after checking your target devices)
Localization	UTF-8 everywhere; non-Latin filenames, emoji, and very long names must work
Accessibility	Large tap targets; screen-reader labels on primary actions
8. Architecture
Transport options considered
Option	Pros	Cons	Verdict
Direct LAN (HTTPS + mDNS)	Fastest, private, no server, works offline	Blocked on isolated/guest/public Wi-Fi, breaks across subnets/VPN	Primary path
WebRTC P2P + signaling	Works across networks, E2E encrypted, no file storage	Needs signaling + TURN server (small cost), NAT complexity	Fallback (M4)
Cloud relay (upload → download)	Simplest to reason about, works anywhere	Cost, privacy, size limits, slower	Avoid as default
Bluetooth / Wi-Fi Direct	No router needed	Slow (BT) / OS-permission pain (Wi-Fi Direct)	Skip for v1; hotspot mode instead
System sketch
LAN: HTTPS + mDNS discovery

Fallback: WebRTC signaling

QR → local HTTPS page

PC app (tray + server)

Phone app

Signaling + TURN server (M4)

Phone browser (web mode)

Every device is both client and server. Each runs a small HTTPS listener and a discovery announcer. The sender opens a session with the receiver, offers a file list, the receiver accepts, and bytes stream in chunks.

Recommended stack
Layer	Recommendation	Why
M0 prototype	Python + FastAPI + uvicorn, qrcode, plain HTML/JS page	No new language, buildable in a weekend
M1+ app	Flutter (one codebase for Android + Windows, iOS later)	LocalSend proves the approach at scale; one codebase for a solo dev
Alternative	Kotlin (Android) + Tauri/Electron (PC)	More native control, but two codebases and two skill sets
Storage	SQLite (local)	History, devices, sessions
Discovery	mDNS (_bridge._tcp) + UDP multicast fallback + manual IP	mDNS alone is unreliable on some routers
Off-LAN (M4)	WebRTC data channels, coturn on a small VPS	Cheap, E2E encrypted
9. Protocol & data model (sketch)
Discovery
mDNS service _bridge._tcp with TXT records: device ID, display name, platform, app version, fingerprint prefix. Devices in Hidden mode don't announce; they can still pair via QR.

Session API (HTTPS, default port configurable with fallback range)
Endpoint	Purpose
GET /v1/info	Device info + capabilities
POST /v1/session	Sender offers files (name, relative path, size, MIME, optional hash). Receiver replies accept/deny + session ID + per-file tokens
PUT /v1/session/{id}/file/{fid}?offset=N	Stream a chunk/range of the file
GET /v1/session/{id}/file/{fid}/status	Bytes confirmed so far (used for resume)
POST /v1/session/{id}/complete	Finalize; receiver verifies hash, renames .part → final
POST /v1/session/{id}/cancel	Abort
POST /v1/snippet	Send text/link/clipboard
Data model (SQLite)
Device {id, name, platform, fingerprint, trusted, pairedAt, lastSeen, lastAddress}
Session {id, peerId, direction, status, totalBytes, createdAt}
FileItem {id, sessionId, name, relPath, size, mime, hash, bytesDone, status, savedPath}
Snippet {id, peerId, direction, kind(text|link|clipboard), body, createdAt}
Rule {id, match(type/source), destination} (P1)
10. Security & privacy
Identity: On first launch each device generates a keypair + self-signed certificate. Pairing exchanges fingerprints out-of-band via the QR code, so a network attacker can't swap keys. After pairing, every connection uses mutual TLS with the pinned fingerprint.

Threat	Mitigation
Stranger on public/hostel/college Wi-Fi pushes files at you	Default: receive from paired devices only. Unknown senders trigger a prompt with rate limiting
MITM during pairing	Fingerprint in QR + on-screen short-code confirmation on both devices
Malicious filenames (..\..\, reserved Windows names like CON, control characters, overlong names)	Strict sanitization; collisions become name (1).ext; never write outside the save root
Dangerous file types (.exe, .bat, .apk, .scr, etc.) from unpaired senders	Warning; never auto-open anything
Disk-fill / DoS	Free-space check before accept; size confirmation for large batches from unknown senders
Lost/stolen phone	Revoke device from the PC; optional app lock (P2)
Signaling/relay server compromise (M4)	End-to-end encryption; server sees metadata only, never content or keys
Device-name leakage	Hidden visibility mode
Privacy rules: no accounts, no telemetry, no cloud on the LAN path, transfer history stored locally with a clear-all option.

11. Platform constraints (these will bite you)
Windows

First listen triggers a firewall prompt; if the network profile is Public, inbound is blocked. The installer should add a Private-network rule and the app should detect and explain the problem.
Unsigned installers trigger SmartScreen warnings (a distribution issue, not a code issue).
Explorer context menu requires registry/shell-extension work (P1).
Android

Scoped storage (Android 10+): use MediaStore/SAF, not raw paths.
Big transfers need a foreground service with a persistent notification and the correct service type declared; OEM battery savers will kill anything else.
mDNS needs a multicast lock; Share Sheet needs ACTION_SEND / ACTION_SEND_MULTIPLE intent filters.
iOS (M4)

Local-network permission prompt, strict background limits, share extensions with tight memory ceilings, App Store review. This is why iOS comes last and web mode exists.
Network

Guest/public/college Wi-Fi often enables client isolation (devices can't see each other). Detect it, tell the user why it failed, and offer hotspot mode or the internet fallback.
VPNs and different subnets/VLANs (PC on Ethernet, phone on Wi-Fi) can break discovery. Manual IP connect (FR-4) is the escape hatch.
12. Test matrix (minimum)
Case	Why
1 KB file, 1 GB file, 10 GB file	Size handling, RAM use
500 small files in one batch	Overhead, UI progress
Nested folder with 3+ levels	Structure preservation
Filenames: non-Latin scripts, emoji, 200+ chars, reserved names	Sanitization, encoding
Wi-Fi drop mid-transfer, app killed mid-transfer, phone screen off	Resume, foreground service
PC on Ethernet, phone on Wi-Fi	Subnet/discovery
Public Network profile on Windows; VPN on	Failure detection and messaging
Two phones paired to one PC	Multi-device handling
Unknown device tries to send	Prompt, rate limit
Disk nearly full on receiver	Pre-accept check
13. Milestones & gates
Estimates assume ~10 hrs/week and are rough.

Milestone	Scope	Time	Exit criteria
M0 – Weekend prototype	Python script on PC: prints QR + URL; phone browser page uploads files to a PC folder, lists a PC "outbox" folder for download, pastes text	2–3 days	Gate: use it for a full week instead of WhatsApp. If you don't, stop and use LocalSend
M1 – MVP	Flutter Windows + Android: discovery, QR pairing, send/receive files + text, share sheet, progress, tray	3–4 weeks	14-day dogfood, meets FR P0 list
M2 – Solid	Resume, hashing, history, folders, save rules, context menu, installer	2–3 weeks	Passes test matrix; 5 friends beta
M3 – Wedge	Clipboard, web mode, hotkey	2 weeks	Feature parity with wedges W1 (LAN part) and W3
M4 – Reach	Off-LAN fallback, iOS	4+ weeks	Relay path E2E encrypted; TestFlight
M5 – Launch	GitHub release, landing page, Play Store	1–2 weeks	Public download
14. Risks
Risk	Likelihood	Impact	Mitigation
Rebuilding LocalSend with no differentiation	High	High	Ship M0 first; commit only to the wedges (persistent feed, creator rules, web mode, off-LAN path)
Android background/OEM restrictions kill transfers	High	High	Foreground service, resume support, test on your own phone's OEM first
Discovery flaky on some routers	Medium	Medium	mDNS + multicast + manual IP + QR-embedded address
iOS friction delays scope	High	Medium	Web mode for iPhone; native iOS last
Windows firewall/SmartScreen scares users	Medium	Medium	Clear first-run guidance; sign the installer before public launch
Scope creep into "Phone Link clone"	Medium	High	Non-goals list is binding
Solo-dev burnout on polish	Medium	Medium	Hard gates at M0 and M1
15. Open questions
Which phone? Android or iPhone (and which Android version/brand)? This decides the entire stack and the MVP.
PC: Windows only? Laptop or desktop, Wi-Fi or Ethernet?
Typical payload: how big are the files you move most (GB-size video vs. photos vs. docs)?
Off-network need: do you regularly need this away from your home Wi-Fi?
Purpose: personal tool, portfolio piece, or a product you'd want to charge for?
License: open source (helps trust and adoption) or closed?
16. MVP (M1) acceptance checklist
 Install on Windows + Android; pair via QR in under 60 s
 Phone → PC: share 10 photos + 1 video from the gallery; originals byte-identical
 PC → phone: drag 3 files; they arrive and open
 Send text/link both directions
 Transfer a 4 GB+ file without memory spikes; cancel works
 Unknown device cannot push files without an explicit accept
 Killing the app mid-transfer leaves no corrupt file in the destination
 History shows all transfers with correct status
 Idle PC app uses < 1% CPU
17. Business notes (later, not now)
Free and ideally open source for the LAN product. If it ever earns money: a hosted relay for off-network transfers (paid tier), or a creator "Pro" pack (rules/automation). Don't think about pricing until it beats LocalSend for your specific wedge.
