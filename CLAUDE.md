# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**SCRAPLINE** — a polished single-file HTML5 Canvas RTS with a persistent-debris twist. The entire game
is `index.html` (~1,015 lines: `<style>` → DOM HUD → one `<script>`). No build, no modules, no
dependencies, no external requests (audio is synthesized via Web Audio; all art is Canvas vector). The
file is intentionally **content-only** (no `<!doctype>/<html>/<head>/<body>`) so it can also be published
as a Claude Artifact.

Design north star: a **rich, StarCraft-like strategy game** (army composition, tech, map control, macro
AI) — *not* an arcade/survival score-chase. See `HANDOFF.md` for current status, the roadmap, and what to
build next; `docs/PLAN.md` has the fuller productionization plan.

## Commands

No build step, test suite, or linter.
- **Run locally:** `python3 server.py` → http://localhost:4180 (or just open `index.html` in a browser).
  `server.py` is a tiny localhost-only static server that serves this folder via `__file__`.
- **Verify (Claude preview MCP):** `preview_start` (reads `.claude/launch.json`) → reload →
  `preview_console_logs level=error` (must be empty) → deterministic headless sims via `preview_eval`
  (`G=new Game(diff)`; loop `G.update(1/60)` N times; assert invariants / no throw / state transitions) →
  `preview_screenshot` desktop and `preview_resize` mobile. The preview viewport sometimes loads at 0–1 px;
  call `resize()` or `preview_resize` to a fixed size first. On macOS the sandboxed preview server cannot
  read files under `~/Desktop` (TCC) and `python3 -m http.server` fails there (blocked `os.getcwd()`); if
  this repo lives under a protected dir, copy `index.html` to a scratch dir and serve it with a
  `__file__`-based `server.py`, pointing `.claude/launch.json` there.

## Architecture (the single-file map)

- **`G` is the world.** One global `G` (a `Game`, created **only** by `startGame(mode, diff)` — the one and
  only `new Game` call site) owns every array (`units`, `buildings`, `projectiles`, `wreckage`, `debris`,
  `nodes`, `selected`), the resources, the queues, fog, and `update(dt)` which steps the whole simulation.
  Entities: `Entity` → buildings (`CommandCenter`/`Silo`/`Turret`/`Foundry`) and units
  (`Harvester`/`Scavenger`, plus a `CombatUnit` base → `Tank`/`Raider`/`Artillery`), plus
  `Shell`/`Wreckage`/`Debris`. Teams are `e.team` (`'player'`/`'enemy'`); `G.enemiesOf(team)` is the targeting helper.
- **App state machine.** `appState ∈ {menu, playing, paused, over}`; `setState()` writes
  `document.body.className`, and CSS uses it to show/hide the `#menu`/`#pause` overlays and the in-game HUD.
  The rAF `loop()` only runs `G.update` while `playing`; `G` is `null` on the menu.
- **Two coordinate spaces.** World pixels (`WORLD_W×WORLD_H` = 3000×1900) vs screen pixels. `render()`
  translates by `-cam.x,-cam.y` (+shake) to draw the world; minimap, fog overlay, and DOM HUD are
  screen-space. `s2w()` converts mouse→world; canvas input handlers convert with it and bail unless `appState==='playing'`.
- **Pathfinding & debris.** `Grid` (CELL=42) runs 8-dir A*; obstacles are reference-counted
  (`block`/`unblock` keep a per-cell count) because wreckage and settled debris both block and may share a
  cell. **Debris blocks paths**; scavengers auto-clear the nearest clutter to keep lanes open. The
  scavenger's per-frame auto-repath is throttled (`repathCd`) with work-range hysteresis (`_working`) + a
  give-up timer to stop it spinning/sticking — don't "simplify" them away.
- **Combat roster & hard counters.** `CombatUnit` (shared acquire/aim/fire) → `Tank` (armored line),
  `Raider` (fast, light), `Artillery` (siege, `splash`). Counters come from `e.cls`
  (`light`/`armored`/`siege`/`building`) × an attacker `bonusVs` multiplier applied in `G.damage` → the
  triangle **Tank > Raider > Artillery > Tank**. Artillery **auto-sieges** after ~1 s idle (2× range &
  damage, swapped in from `baseRange`/`baseDmg`, deployed visual). **Mind the `instanceof` split:** tank
  *upgrades* (`applyAllUpg`/`buyUpgrade`) are Tank-only, but right-click attack orders, double-click-select,
  and the AI "army" use `instanceof CombatUnit`.
- **Tech tier & node economy.** A **Foundry** (built from the CC BUILD cluster) raises tech; `hasTech(team)`
  gates Artillery. Resource nodes hold one of 5 richness levels (`NODE_MAX`); the node draws a 5-crystal
  fullness gauge, left-click inspects it (`nd._show`), and `spawnNode()` drops a fresh node every 300 s (`G.nextNode`).
- **Timed production differs by team.** Player builds/upgrades go through queues: `G.queue` (units, with
  per-type build times + the parts-fueled `G.boost` overclock) and `G.upgQueue.player` (tank-upgrade
  research, escalating cost via `upgCommitted`). **The AI does NOT use the player queue** — it spawns
  instantly on its own cadence timer in `AI.update` (its upgrades queue via `upgQueue.enemy`). Difficulty
  is the `DIFF` table (easy/normal/hard), read by both `AI` and `Game`.
- **HUD is DOM, synced each frame** by `syncHUD()`/`syncProd()`. The Command-Center build/upgrade menu
  (`#smenu`) shows only while a player CC is selected.

## Gotchas (keep these guards)

- **Accidental "restart mid-game" via focused overlay buttons (this bit twice).** Overlays hide with
  `opacity:0`, not `display:none`, so their buttons keep keyboard focus and a stray Space/Enter re-fires
  them. Defenses — keep ALL of them: Space/Enter are `preventDefault`ed in keydown; buttons are blurred on
  click/keydown/canvas-mousedown; and **`startGame`/restart are gated on `appState`** (restart only from
  `over`, ~600 ms debounce; start only from `menu`).
- **The CSP `<meta>` is head-only by design** — it hardens the served file but is ignored inside a
  published Artifact (the platform wraps content in `<body>`). Safe in both; don't "fix" it by moving it.
- **Content-only on purpose** — keep all CSS/JS inline; any external request would break both the Artifact
  CSP and the self-host CSP.
- **Balance numbers are a first pass, not human-playtested** — tune with the user rather than blindly.

## Status & roadmap
`HANDOFF.md` is the living status doc: what's done, the pending roadmap (next big item: **4× map + up to 3
colored free-for-all AIs**), and the design decisions behind the game.
