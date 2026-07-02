# SCRAPLINE — Production-Readiness Plan

## Context
`scrapline/index.html` is a complete, fun single-file HTML5 Canvas RTS, but it's been validated only by headless simulation, not by real players on real devices. The goal of this work is to close the gap from "impressive prototype" to "something you can hand to a stranger (on a phone) and it just works, looks intentional, and holds up." The user selected a near-full productionization pass and added "fix security and performance issues." Two-device multiplayer is **deferred** — the published Claude Artifact runs under a strict CSP that blocks all networking, so MP needs a self-hosted server + RTS netcode (a separate project). For now the home screen gets a clearly-marked, disabled "2-Player (coming soon)" slot so the menu is MP-ready.

Distribution constraint that shapes everything: the game ships as **one self-contained file** (no external requests) so it can be published as an Artifact. All work must preserve that.

## Scope (selected by user)
**Build:** Home screen + onboarding · Responsive HUD · Pause + autosave · Touch/mobile · Performance pass · Difficulty levels · Audio mute/volume · Match-feel polish (rally/cancel-queue/control-groups) · End-of-match stats · Share meta tags · Cross-browser + code-split · **Security + performance hardening** (custom).
**Defer:** Online 2-device MP (menu slot only). **Skip:** Colorblind palette (not selected).

All edits are in `scrapline/index.html` unless noted. After each milestone: copy to the scratchpad server dir, reload the preview, check console for errors, run a deterministic sim, screenshot, then re-publish the Artifact (same URL).

---

## Workstream A — App state machine (foundation; prerequisite for B/C/D)
Today `G = new Game()` runs at load and `loop()` always calls `G.update`. Introduce a top-level `appState ∈ {menu, playing, paused, over}` and a `startGame(mode, difficulty)`.
- `loop()`: branch on `appState` — `playing` → update+render+HUD; `paused`/`over` → render only (frozen); `menu` → render menu backdrop only. Guard all `G.*` access when `G` is null (menu before first start). Keep the existing crash-guard `try/catch`.
- `Game.endGame()` → set `appState='over'` (it already drives the `#over` overlay).
- Bottom-of-file init: show menu instead of auto-starting.

## Workstream B — Home screen + onboarding + difficulty + MP slot
- New `#menu` HTML overlay (sibling of `#over` in `#ui`): title "SCRAPLINE", one-line pitch, **win condition** ("Destroy the enemy Command Center"), a compact controls/legend, a **Mode** row (`Vs AI` enabled; `2-Player · 2 devices — coming soon` disabled), a **Difficulty** row (Easy/Normal/Hard), and a START button. Reuse `.btn`/pill styling.
- Difficulty plumbing: `startGame` stores `G.difficulty`; `AI` constructor reads a preset table tuning `wave` start, attack `grace` (currently `G.time>45`), `attackCd`, economy cadence `this.t`, and `Game` starting `aiRes`/starting forces. Easy = passive/poor; Hard = aggressive/rich + earlier upgrades.
- First-run tooltips: lightweight, dismissible hints keyed off first selection / first build (optional, low priority within this stream).

## Workstream C — End-of-match stats
- Add counters to `Game`: `stats = {built, lost, scrapScavenged, partsScavenged}`. Increment in `kill()` (when a player unit dies → `lost`), `clearClutter()` (player → scrap/parts scavenged), `spawn()`/queue-complete (built).
- `endGame()` populates `#osub`/new stat rows on `#over`, including match time (`G.time`).

## Workstream D — Pause + autosave (depends on A)
- Pause: a HUD pause button + key `P` → toggle `appState` playing⇄paused; show a `#pause` overlay (Resume / Quit to menu).
- Autosave to `localStorage` key `scrapline.save.v1`: `Game.serialize()` snapshots **essentials only** — `difficulty, time, playerRes/aiRes/playerParts/aiParts, upg, queue, boost, cam`, `nodes` (x/y/amt), `buildings` (kind/team/x/y/hp), `units` (class/team/x/y/hp/angle + per-class fields: tank turret/attackTarget-id, harvester load/state, scavenger targets), `wreckage` (x/y/mode), `debris` (x/y/settled), and `fog` (Uint8Array → base64). Skip transient FX (`parts`, `texts`, `decals`).
- `Game.fromSave(obj)`: rebuild via constructors then assign fields; re-block grid cells for wreckage/settled-debris; rebuild fog. Resolve `attackTarget` ids after all units exist.
- Save cadence: every ~5s while `playing`, and on `visibilitychange`/`pagehide`. On menu load, if a valid save exists, show a **Resume** button.
- **Security**: wrap `JSON.parse` in try/catch; validate `v` and shape; on any mismatch/corruption, discard the save (never trust/execute it). No `eval`/`Function`.

## Workstream E — Responsive HUD (CSS)
- Fix the real bug: `#hint` (top-center) overlaps `#top` pills on narrow widths. Reflow: stack/scale pills, move or hide `#hint` under a threshold, ensure `#bar` + `#smenu` + `#prod` + minimap don't collide.
- Add `@media (max-width: 900px)` and a very-narrow tier: shrink pill text, wrap `#smenu`, shrink/relocate the minimap, scale the bottom bars. Verify with `preview_resize` mobile/tablet presets.

## Workstream F — Audio mute/volume
- Route `Audio2` through a master `GainNode` (currently each sound connects straight to `destination`). Add `Audio2.setVolume()/toggleMute()`.
- HUD mute button (top-right area near minimap) + persist in `localStorage`.

## Workstream G — Security hardening (custom request)
- Add a strict **CSP `<meta http-equiv>`** to the standalone file: `default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'` — the game is fully self-contained, so this blocks any injected external load/exfiltration. (The Artifact enforces its own CSP; this hardens the self-hosted copy.)
- Audit all dynamic DOM writes use `textContent` (they do today) — keep it that way; no `innerHTML` with dynamic data.
- Guarded save-load (see D). `scrapline/server.py` already binds `127.0.0.1` (not exposed); add a short comment noting it's a localhost dev server only.

## Workstream H — Performance pass (custom request + selected)
Concrete hot paths confirmed in code:
- `enemiesOf(team)` allocates a fresh array (spread of two filters) and is called **every frame per shell** (`Shell.update`) and by turret/tank targeting. Replace with a **once-per-frame cached enemy list per team** (built in `Game.update`) and/or a **uniform-grid spatial hash** for radius queries.
- `Unit.separate()` is **O(n²)** over all units each frame → query the spatial hash for nearby units only.
- Targeting (`Tank.acquire`, `Turret.update`, `Shell` proximity) uses the same spatial hash for nearest-enemy.
- Verify with a deterministic 50-vs-50 sim measuring per-step cost (proxy for fps) before/after.

## Workstream I — Match-feel polish
- **Rally points**: when the CC is selected, right-click sets `cc.rally`; `spawn()`/queue-complete moves new units toward it. Draw a rally flag.
- **Cancel queued unit + refund**: a ✕ on `#prod` (and right-click the panel) removes the last queued item and refunds its scrap.
- **Control groups**: Ctrl+`1..9` assign, `1..9` select. **Conflict**: `1/2` place structures and `3/4/5` buy upgrades. Resolution — rebind structure/upgrade shortcuts off the number row (e.g., structures `Z`/`X`, upgrades `R`/`F`/`C`, or menu-click only) and free `1..9` for control groups. Update the legend/onboarding accordingly.

## Workstream J — Touch / mobile controls (largest)
- Detect touch (`pointerdown`/`'ontouchstart'`) and switch input scheme; convert mouse handlers to Pointer Events where shared.
- Scheme: **one-finger tap** = select unit/building; **one-finger drag on empty** = box-select; if units are selected, **tap a target** = context command (move / attack enemy / clear clutter / repair ally — reuse `pickEnemy`/`pickClutter`/`pickDamagedAlly`); **double-tap** own unit = select all combat on screen; **two-finger drag** = pan camera; **tap minimap** = jump. Existing on-screen buttons (build bar, `#smenu`, `#boost`, pause) are already tappable.
- Placement mode: tap to place, on-screen Cancel.
- Layout depends on E (responsive). Note: final UX needs a **real-device test** (cannot be fully automated); simulate with `preview_resize` mobile + dispatched pointer events.

## Workstream K — Cross-browser + code organization + smoke test
- Cross-browser audit: `webkitAudioContext` already handled; verify Pointer Events, `Uint8Array`/base64 save, `KeyboardEvent` handling on Safari/Firefox. Fix any gaps.
- **Code split vs single-file tension**: keep single-file distribution. Recommended: split source into `scrapline/src/*.js` and add a **Python concat build** (`scrapline/build.py`, no Node dependency available in this env) that inlines them into `index.html` between markers. This gives module-level maintainability while preserving the one-file Artifact.
- **Smoke test**: formalize the deterministic preview sim as `scrapline/smoke.md` (a documented `preview_eval` routine: fresh game, run N frames headless, assert no error + invariants like `over` only on CC death, save→reload round-trip equality). Run it as the regression check after each milestone.

---

## Suggested execution order
A → B → C → D → E → F → G → H → I → J → K. (Foundation first; touch last since it builds on a stable, responsive input/HUD layer.) Given the size, this will land as a sequence of milestones, each verified and re-published, not one drop.

## Verification (per milestone, via Claude Preview MCP)
1. Copy `index.html` to the scratchpad server dir; `preview_start`/reload; `preview_resize 1280×800`.
2. `preview_console_logs level=error` → must be empty.
3. Deterministic `preview_eval` sims: state-machine transitions (menu→play→pause→over→menu); difficulty presets change AI params; **save→reload round-trip** reproduces unit/resource/fog counts; perf sim 50v50 step-cost before/after; rally/cancel/control-group logic; end-stats counters.
4. `preview_screenshot` at desktop **and** `preview_resize` mobile/tablet for the home screen, responsive HUD, and touch layout.
5. Re-publish the Artifact (same URL) once green.
6. Manual: one real touch-device pass for Workstream J (flagged — not automatable here).

## Deferred / follow-up
- **Online 2-device MP**: WebSocket relay or authoritative-host + deterministic/lockstep netcode; self-hosted only (not the Artifact). Menu slot is built MP-ready.
- **Colorblind palette**: not selected; easy to add later (team shapes already differ).
- Real-player playtesting for fun/balance remains the one thing simulation can't validate.
