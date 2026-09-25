Bridge — Design System

Monumental type on warm concrete

Source style: Elva (Refero Styles) · Applied to: Bridge — Windows app, Android app, browser "web mode" Theme: light only (v1) Scope: visual system only. All copy comes from the product; labels shown here are placeholders.

Legend: [S] = taken directly from the source style. [A] = adapted, because the source is a marketing site and Bridge is a utility app. Where they conflict, [S] tokens win and [A] rules must not break the [S] look.

1. Principles
Type is the interface. Hierarchy comes from size and weight only, never from color. [S]
One ink, one paper. Warm Obsidian on Bone White. No accent color anywhere. [S]
Negative space is the layout. No cards, no shadows, no gradients, no dividers except hairlines. [S]
Actions are text links with an arrow. No filled or outlined buttons. [S]
One monument per screen. Each screen has exactly one oversized typographic element; everything else is quiet. [A]
Raw over decorated. No illustration, no icon sets. The only graphics are pictogram glyphs set inline with display type. [S]
2. Color
Name	Hex	Token	Role
Warm Obsidian
#262523	--color-ink	All text, glyph strokes, focus rings, progress fill, active borders. The only ink
Bone White
#ececec	--color-canvas	Every screen background and primary surface
Pale Ash
#cfcdcd	--color-ash	Hairlines, idle borders, progress track, the rare nested surface
Pure Black
#000000	--color-black	Tiny marks only (e.g., QR quiet-zone check). Never for text

Rules

Body and display text is always
#262523, never
#000000. [S]
No chromatic color in the UI. The only colored pixels on screen are the user's own photos and videos. [A]
Warm Obsidian on Bone White is ≈ 13:1 contrast. Pale Ash on Bone White is ≈ 1.3:1: decoration only, never text, never the sole carrier of a state. [A]
State without color: success, error, and selection are expressed with words, weight, border darkness, and arrow glyphs (Section 6). [A]
Interaction opacity: pressed/hover 0.6 over 200 ms [S]; disabled 0.35. [A]
Dark theme is deliberately deferred. If added later it is a strict inversion of these four tokens, and nothing else changes. [A]
3. Typography

Primary: Basis Grotesque [S] — commercial typeface. Ship Inter (the source's stated free substitute), Manrope as alternate. Use Inter's tabular figures for all numerals that change. [A] Display alt (Messina Sans): not used inside the app. Reserved for a marketing page only. Weights: 400 body and display · 500 labels and links · 700 wordmark and rare emphasis. [S]

Scale
Token	Size	Line height	Tracking	Weight	Use
monument	phone 72–96 px · desktop 160 px	0.82	−0.06em	400	The one oversized element per screen [S/A]
heading	phone 48–64 px · desktop 120 px	0.90	−0.06em	400	Secondary large moments, empty states [S/A]
heading-sm	40 px	1.0	−0.04em	400	Screen sub-titles, pairing short-code [S]
subheading	32 px	0.9	−0.04em	400	Device names, primary action links [S]
body	15 px	2.0 (prose) · 1.4 (dense rows)	−0.02em	400	Paragraphs use 2.0 [S]; list rows use 1.4 [A]
link	15 px	1.2	−0.02em	500	Text link + arrow [S]
label	12 px, UPPERCASE	1.2	−0.02em	500	Nav, section labels, pills [S]
caption	12 px	1.2	−0.02em	400	Speed, ETA, timestamps [A] (source uses 10 px)
wordmark	32 px	1.0	−0.04em	700	Top-left identity [S]

Rules

Nothing in the app below 12 px. 10 px is reserved for splash/footer only. [A]
Display sizes (≥ 120 px desktop): line-height ≤ 0.90, tracking ≤ −0.06em. This compression is the signature. [S]
Monument text is fluid, not stepped: clamp(72px, 22vw, 160px). [A]
Body paragraphs max-width 480 px. Display type has no max-width and bleeds to the left edge. [S]
Left-aligned always. Never centered. [S]
Numerals that update (percent, speed, ETA) use font-variant-numeric: tabular-nums so they don't jitter. [A]
Respect OS font scaling up to 200%. Monument text may shrink to its clamp floor, body must reflow. [A]
4. Spacing, shape, layout

Base unit: 8 px · Density: spacious [S]

Token	Desktop	Phone	Notes
Edge padding	40	20	Source uses 40 px from viewport edges [S/A]
Element gap	16	16	[S]
Section gap	80	48	Source minimum is 80 [S/A]
Above monument	160	96	[S/A]
Nested surface padding	40	24	Drop zone, QR block [S/A]

Spacing scale: 8 · 16 · 24 · 40 · 48 · 80 · 160 · 240

Radius: 10 px for every nested surface, input, and container [S] · 70 px only for pills [S] · progress lines and hairlines are square [A]

Layout

Full-bleed, single column, left-aligned, no visible grid, no sidebar, no cards. [S]
Sections separated by whitespace first, a 1 px Ash hairline only when a list needs rhythm. [S/A]
Desktop window: default 480 × 720, resizable, content stays left-aligned and single-column. It behaves like a tray utility, not a dashboard. [A]
Phone: top text-nav, no bottom tab bar, no icons in navigation. [A]
5. Surfaces & elevation
Level	Name	Value	Purpose
0	Canvas
#ececec	Every screen
1	Subtle surface
#cfcdcd	Rare band or nested area (drop zone border, progress track)

No shadows. No gradients. No blur. No scrims. [S] If something must feel "above", make it larger and tighter, or take over the whole canvas. Modals become full-canvas takeovers, not floating cards. [A]

Amendment 24 Sep 2026 (owner override): restrained warm elevation allowed on nested surfaces only — dropzone (`--shadow-1`, `--shadow-2` on drag) and photo thumbnails (`--shadow-thumb`). Ink at low alpha, never colored glow. Canvas, pills, rows stay flat. Tokens in `css/tokens.css`.

Amendment 25 Sep 2026 (owner override): Apple-like structure WITHOUT color. Monochrome palette (§2) is binding — Warm Obsidian on Bone White, no accent, no blue. Adopted from Apple: SF system font stack first, filled primary buttons (Ink fill, Canvas text), 17 px body for UI text, card surfaces (Canvas fill, Ash hairline, 12–16 px radius) for rows/zones, bottom tab bar on phone. Rolled out one surface per branch in `css/apple.css`; base tokens and text-link components stay until their slice lands.

6. Components
Wordmark [S]

Product name in Basis/Inter 700, 32 px,
#262523, top-left at edge padding. No symbol. A 12 px sub-line is optional.

Top navigation [S/A]

Row of text links: label style (12 px, 500, uppercase, −0.24 px), 40 px gap, no background, no underline, no border. Current screen = full opacity, others 0.6. Pinned to the top edge; entire upper third of a fresh screen is left as negative space.

Text link with arrow — the only action pattern [S]
Text in link (15 px/500) or subheading (32 px/400) followed by → in the same size and color.
Action hierarchy is size, not color: primary action at 32 px, secondary at 15 px. [A]
Pressed/hover: opacity 0.6, 200 ms. [S]
Hit area: minimum 48 × 48 (px on desktop, dp on Android), achieved with invisible padding, never a visible box. [A]
Keyboard/screen-reader focus: 2 px solid Warm Obsidian outline, 4 px offset, radius 10. [A]
The arrow is decorative (aria-hidden); the text is the accessible label.
Monument [S/A]

The single oversized text element per screen (monument or heading token), placed ~96–160 px below the top edge, left-bleeding, words stacked in lines. Content examples per screen are in Section 8. May end with a period, as in the source. May carry one pictogram glyph.

Pictogram glyph [S/A]

Monochrome line-art, no fill, stroke ≈ 5% of the font size (6–8 px at 160 px), Warm Obsidian, sized to cap-height, replaces one letter in monument/heading text. Never standalone, never functional, never in body text. Make a small custom set of 4–5 (suggested: asterisk, arch, double-arrow, circle-dot, spark). Use them at moments of emptiness or completion, not on every screen.

Section label pill [S]

label text, Bone White background, 1 px Ash border, radius 70, padding 6 × 12. Wayfinding and status only. Not tappable.

Status without color [A]: neutral statuses (PAIRED, LAN, IN, OUT) use the Ash border. Attention statuses (FAILED, PAUSED, RELAY) use a 1 px Warm Obsidian border. Words carry the meaning; the border only adds weight.
Device row [A]

Name in subheading (32 px), platform in label above or beside, status pill at the end. Min height 72 (phone 64). 1 px Ash hairline between rows. Selected state: trailing → appears and name goes to weight 500. No checkboxes, no fills, no highlights.

Drop zone (desktop) [A]

The one permitted nested surface: transparent fill, 1 px Ash border, radius 10, 40 px padding, minimum height 240.

Idle: label text only.
Drag-over: border becomes 2 px Warm Obsidian, inner text swaps to heading-sm.
No dashed lines, no icon, no upload cloud.
Transfer progress [A]
Numeral: percentage in monument/heading, tabular figures. It is the progress indicator.
Line: 2 px tall, full width, Ash track, Warm Obsidian fill, square ends, no animation easing beyond linear updates.
Meta: filename in body, speed and ETA in caption on one line.
Actions: → text links (secondary size), e.g., cancel/pause.
Batch: list of files, each with a 1 px progress line under its name; the monument shows the batch percentage.
History row [A]

Timestamp caption, filename body, direction as an IN/OUT pill (no icons), size caption. Optional 48 px square thumbnail, radius 10, no border, original color (the only chromatic content allowed). 1 px Ash hairline between rows. Re-send is a secondary → link.

Pairing block [A]

QR code rendered Warm Obsidian on Bone White, quiet zone ≥ 4 modules, square modules only (no rounded or styled QR, it hurts scan reliability). Sits in a nested surface (1 px Ash border, radius 10, padding 40/24). The confirmation short-code below it is set in heading-sm, tabular figures.

Incoming-request takeover [A]

Full-canvas screen on phone; on desktop a fixed-size window, or a notification-style panel: Bone White, 1 px Warm Obsidian border, radius 10, no shadow. Sender name in monument/heading; primary action link at 32 px, decline at 15 px.

Inputs [A]

Transparent fill, 1 px Ash border, radius 10, 15 px text, 16 px vertical / 16 px horizontal padding. Label in caption above, always visible (no floating labels). Focus: border becomes 2 px Warm Obsidian. Error: text label beneath in caption plus border 2 px Obsidian; the message states the problem in words.

Settings rows [A]

Label left in body, value right as a text link (ON → / OFF →) that toggles on tap. No switches, no checkboxes. Expose as a switch role to assistive tech.

Empty state [A]

heading text, optional single pictogram glyph in that text, one → link. No illustration.

Toast / snackbar [A]

Bone White, 1 px Warm Obsidian border, radius 10, no shadow, body text, one optional → link. Auto-dismiss 4 s, fades over 200 ms.

7. Motion
Only opacity and position, 200 ms, ease-out. [S]
No springs, bounces, scale pops, or parallax. [A]
Screen changes: 200 ms crossfade. [A]
Progress numerals update in place with no tweening. [A]
Honor "reduce motion": drop fades to instant. [A]
8. Screen compositions (layout only)
Screen	Monument	Primary action (32 px)	Structure below
Home	Active device name or the drop prompt	Send →	Device rows, then recent-transfers hairline list
Transfer	Percentage numeral	(none while running)	Progress line, meta, batch list, cancel link
Pair	The short-code or the QR's heading	Scan → / Confirm →	QR nested surface, fingerprint
Incoming	Sender name	Accept →	Decline link, file list in body, size in caption
History	Day/group heading at heading size	(none)	Hairline rows
Settings	heading screen title	(none)	Label + → value rows, section labels as pills
Web mode (phone browser)	Session heading	Choose files →	Same tokens; single column; no app chrome

Each screen: top whitespace → monument → one primary action → quiet secondary content. Never two competing large elements.

9. Imagery & icons
No photography, illustration, or decorative graphics. [S]
No UI icons of any kind: nav, buttons, status, list rows. Words and arrows only. [S]
OS-required exceptions [A]: app icon (Bone White field, Warm Obsidian pictogram), Android notification small-icon (monochrome silhouette of the same pictogram), Windows tray icon (monochrome). These are the only icons in the product.
10. Do / Don't
Do
Use display type with line-height ≤ 0.90 and tracking ≤ −0.06em. [S]
Keep every pixel of UI in
#262523 on
#ececec, with
#cfcdcd for hairlines. [S]
Make every action a text link followed by →. [S]
Keep body prose at 15 px with airy leading and ≤ 480 px width. [S]
Use size and weight to show hierarchy and state. [S]
Give every screen one monument and lots of empty space. [A]
Give every link a 48 px hit area and a visible focus ring. [A]
Don't
Don't add filled or outlined buttons, switches, checkboxes, FABs, chips with fills. [S]
Don't add shadows, gradients, blur, or dimmed scrims. [S]
Don't use
#000000 for text. [S]
Don't center text or constrain display type to a container. [S]
Don't use color to signal success, error, or selection. [S/A]
Don't use line-height above 1.0 on display type. [S]
Don't use icons in the traditional UI sense; pictograms live inline in display type only. [S]
Don't put text in Pale Ash. [A]
11. Known tradeoffs (decide early)
No buttons + no color = weaker affordance. Mitigate with size hierarchy, arrows, and generous hit areas; usability-test the primary Send flow on a real phone before polishing anything else.
Monochrome status. Errors rely on words and border weight. Keep messages explicit.
Monumental scale on a phone is compressed by design (clamp), so treat the phone as the source of truth and desktop as the expansion.
12. Tokens
CSS custom properties (web mode + M0 prototype)
css
:root {
  /* Color */
  --color-ink: #262523;
  --color-canvas: #ececec;
  --color-ash: #cfcdcd;
  --color-black: #000000;

  /* Fonts */
  --font-primary: 'Basis Grotesque', 'Inter', 'Manrope', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-bold: 700;

  /* Type */
  --text-monument: clamp(72px, 22vw, 160px);
  --leading-monument: 0.82;
  --tracking-monument: -0.06em;

  --text-heading: clamp(48px, 11vw, 120px);
  --leading-heading: 0.9;
  --tracking-heading: -0.06em;

  --text-heading-sm: 40px;
  --leading-heading-sm: 1;
  --tracking-heading-sm: -0.04em;

  --text-subheading: 32px;
  --leading-subheading: 0.9;
  --tracking-subheading: -0.04em;

  --text-body: 15px;
  --leading-body: 2;      /* prose */
  --leading-ui: 1.4;      /* dense rows */
  --tracking-body: -0.02em;

  --text-label: 12px;
  --text-caption: 12px;
  --leading-small: 1.2;

  /* Spacing */
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-5: 40px;
  --space-6: 48px;
  --space-10: 80px;
  --space-20: 160px;
  --edge: 20px;
  --section-gap: 48px;
  --above-monument: 96px;
  --surface-pad: 24px;
  --hit-min: 48px;

  /* Shape */
  --radius-surface: 10px;
  --radius-pill: 70px;
  --hairline: 1px solid var(--color-ash);

  /* Motion */
  --duration: 200ms;
  --ease: ease-out;
  --opacity-pressed: 0.6;
  --opacity-disabled: 0.35;
}

@media (min-width: 720px) {
  :root {
    --edge: 40px;
    --section-gap: 80px;
    --above-monument: 160px;
    --surface-pad: 40px;
  }
}

body {
  background: var(--color-canvas);
  color: var(--color-ink);
  font-family: var(--font-primary);
  font-variant-numeric: tabular-nums;
  text-align: left;
}
Flutter mapping (M1 app)

Flutter letterSpacing is in logical pixels (em × font size) and height is a multiplier.

dart
const ink = Color(0xFF262523);
const canvas = Color(0xFFECECEC);
const ash = Color(0xFFCFCDCD);

// Desktop values shown; scale monument/heading with MediaQuery width.
const monument   = TextStyle(fontFamily: 'Inter', fontSize: 160, height: 0.82, letterSpacing: -9.6, fontWeight: FontWeight.w400, color: ink);
const heading    = TextStyle(fontFamily: 'Inter', fontSize: 120, height: 0.90, letterSpacing: -7.2, fontWeight: FontWeight.w400, color: ink);
const headingSm  = TextStyle(fontFamily: 'Inter', fontSize: 40,  height: 1.0,  letterSpacing: -1.6, fontWeight: FontWeight.w400, color: ink);
const subheading = TextStyle(fontFamily: 'Inter', fontSize: 32,  height: 0.9,  letterSpacing: -1.28, fontWeight: FontWeight.w400, color: ink);
const body       = TextStyle(fontFamily: 'Inter', fontSize: 15,  height: 2.0,  letterSpacing: -0.3, fontWeight: FontWeight.w400, color: ink);
const label      = TextStyle(fontFamily: 'Inter', fontSize: 12,  height: 1.2,  letterSpacing: -0.24, fontWeight: FontWeight.w500, color: ink);

Theme-level: scaffoldBackgroundColor: canvas, useMaterial3: false, splash/highlight/hover colors transparent, elevation 0 everywhere, and implement links as InkResponse-free tappable text with an opacity animation instead of Material buttons.

13. Agent prompt guide

Quick reference: text
#262523 · canvas
#ececec · hairline
#cfcdcd · accent none · primary action = 32 px text link with →.

Example prompts:

Monument: "Left-aligned, bleeding to the edge, Inter 400, clamp(72px, 22vw, 160px), line-height 0.82, letter-spacing −0.06em, color
#262523, words stacked in lines, placed 96 px below the top. One letter may be replaced by a line-art pictogram at cap-height."
Action link: "Inter 500, 32 px,
#262523, no underline, followed by → in the same size. Hover/pressed opacity 0.6 over 200 ms. 48 px minimum hit area via padding. Focus: 2 px solid
#262523 outline, 4 px offset."
Device row: "Name at 32 px/0.9, platform in 12 px uppercase label, status as a pill (1 px
#cfcdcd border, radius 70, 6×12 padding). 1 px
#cfcdcd hairline between rows. Selected = trailing → and weight 500, no fill."
Progress: "Percentage in monument size with tabular numerals, below it a 2 px line with
#cfcdcd track and
#262523 fill, square ends. Filename 15 px, speed and ETA 12 px on one line. Cancel as a 15 px text link with arrow."
Drop zone: "Transparent, 1 px
#cfcdcd border, radius 10, min height 240, 40 px padding. On drag-over, border becomes 2 px
#262523. No dashed lines, no icon."
