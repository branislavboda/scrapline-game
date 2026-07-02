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

- **`G` is the world.** One global `G` (a `Game`, created **only** by `startGame(cfg)` — the one and
  only `new Game` call site) owns every array (`units`, `buildings`, `projectiles`, `wreckage`, `debris`,
  `nodes`, `relays`, `selected`), the resources, the queues, fog, and `update(dt)` which steps the whole simulation.
  Entities: `Entity` → buildings (`CommandCenter`/`Silo`/`Turret`/`Foundry`) and units
  (`Harvester`/`Scavenger`, plus a `CombatUnit` base → `Tank`/`Raider`/`Artillery`), plus
  `Shell`/`Wreckage`/`Debris`.
- **N-team free-for-all.** `G.teams` = `['player','ai1',…]` (1 human + 1–3 AIs, set by `CFG.numAIs`);
  `G.aiTeams` is the rest, each with its own `AI` in `G.ais`. **Per-team state is keyed maps**, not scalar
  pairs: `G.res[t]`, `G.parts[t]`, `G.upg[t]`, `G.upgQueue[t]`. `G.enemiesOf(team)` returns **everyone not on
  `team`** (true FFA — AIs fight each other). Per-team colors via `TEAM_COL`/`TEAM_DARK` (player cyan, ai1
  red, ai2 orange, ai3 purple); `teamCol()`/`teamDark()` are table lookups. **Win = all rival CCs gone
  (`'player-win'`), lose = player CC gone (`'player-lose'`)** — `endGame(result)` branches on that token.
- **App state machine.** `appState ∈ {menu, settings, playing, paused, over}`; `setState()` writes
  `document.body.className`, and CSS uses it to show/hide the `#menu`/`#setup`/`#pause` overlays and the
  in-game HUD. The rAF `loop()` only runs `G.update` while `playing`; `G` is `null` on the menu/settings.
- **Match Setup screen + `CFG`.** The menu's "SET UP MATCH ▸" opens `#setup` (appState `settings`), a
  slider/toggle panel bound to a central **`CFG`** object (defaults in `CFG_DEFAULTS`, persisted to
  `localStorage` `scrapline.cfg`). `CFG` is the UI↔sim contract — game speed, starting scrap/parts,
  node richness/count, AI difficulty preset + count + aggression/economy overrides, supply-cap base, start
  army, fog on/off, base placement. `Game`, `AI`, `loop()` and `popCap()` all read it. Game speed is a `dt`
  multiplier in `loop()` (raw frame delta stays clamped at 0.04; camera uses the unscaled delta).
- **Two coordinate spaces.** World pixels (`WORLD_W×WORLD_H` = 6000×3800) vs screen pixels. `render()`
  translates by `-cam.x,-cam.y` (+shake) to draw the world; minimap, fog overlay, and DOM HUD are
  screen-space. `s2w()` converts mouse→world; canvas input handlers convert with it and bail unless `appState==='playing'`.
  `layoutMap({numTeams,nodeCount,placementStyle,richness})` places CCs on an ellipse ring + scatters nodes.
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
- **Upgrades affect Turrets too + are visible.** The range/armor/power research applies to Tanks (via
  `applyUpgDelta`) **and Turrets** — turret range/dmg derive live from `G.upg[team]` in `Turret.update`;
  armor bumps turret maxhp in `completeUpg` and at placement. Each upgrade **changes the draw**: range =
  longer barrel, power = thicker/brighter barrel, armor = extra plating + size.
- **Veterancy.** `Shell` carries its `owner`; `G.damage(e,dmg,team,bonusVs,attacker)` credits the killer,
  `G.promote()` ranks CombatUnits (2/5/9 kills → vet 1/2/3, +hp/+dmg; `baseDmg` bumped too so Artillery
  siege recompute keeps it). Veterans draw gold chevrons (`vetBadge`) + grow (`vscale`).
- **Buildings take time to build.** Structures placed via `placeStructureAt` start `built=false` at ~15% HP,
  ramp over 6–12 s (progress ring + countdown), are **attackable and inert until done** (`popCap`/`hasTech`
  ignore unbuilt; unbuilt turrets don't fire). The construction tick lives in the `update` building loop.
- **Tech tier & node economy.** A **Foundry** (built from the CC BUILD cluster) raises tech; `hasTech(team)`
  gates Artillery. Resource nodes hold one of 5 richness levels (`NODE_MAX`); the node draws a 5-crystal
  fullness gauge, left-click inspects it (`nd._show`), and `spawnNode()` drops a fresh node every 300 s (`G.nextNode`).
- **Two currencies + map control.** Scrap **and** spare parts. Costs live in shared tables
  `UNIT_COST/UNIT_TIME/UNIT_PARTS` + `STRUCT_COST/STRUCT_PARTS` — Artillery/Foundry cost **+40 parts**,
  Turret/Silo **+15**; parts gate the tech army. Parts are earned by scavengers clearing clutter
  (`clearClutter`). A capturable center **Relay** (`G.relays`, `updateRelays`) grants the uncontested holder
  a scrap+parts income trickle + vision — it's the decisive map-control objective. A **"scrapline collapse"**
  (`SUDDEN_T=240`) decays all CCs after 4 min so no match stalemates.
- **Timed production differs by team.** Player builds/upgrades go through queues: `G.queue` (units, with
  per-type build times + the parts-fueled `G.boost` overclock) and `G.upgQueue.player` (tank-upgrade
  research, escalating cost via `upgCommitted`). **The AIs do NOT use the player queue** — each spawns
  instantly on its own cadence timer in `AI.update` (its upgrades queue via `upgQueue[aiTeam]`; it scores
  target CCs — weakest/closest/retaliate/anti-gang — and sometimes rushes the Relay). Difficulty is the
  `DIFF` table (easy/normal/hard) + `CFG` aggression/economy overrides, read by both `AI` and `Game`.
- **HUD is DOM, synced each frame** by `syncHUD()`/`syncProd()`. The Command-Center build/upgrade menu
  (`#smenu`) shows only while a player CC is selected.

## Gotchas (keep these guards)

- **Accidental "restart mid-game" via focused overlay buttons (this bit twice).** Overlays hide with
  `opacity:0`, not `display:none`, so their buttons keep keyboard focus and a stray Space/Enter re-fires
  them. Defenses — keep ALL of them: Space/Enter are `preventDefault`ed in keydown; buttons are blurred on
  click/keydown/canvas-mousedown; and **`startGame`/restart/state transitions are gated on `appState`**
  (restart only from `over`, ~600 ms debounce; open setup only from `menu`; start only from `settings`).
  Every new `#setup` button blurs on click and is appState-gated — keep that.
- **Per-team state is keyed maps, not scalars.** It's `G.res[t]`/`G.parts[t]`/`G.upg[t]`/`G.upgQueue[t]`
  (keyed over `G.teams`), NOT the old `playerRes`/`aiRes`. `'player'` stays a team key so player-only paths
  (HUD, build queue, fog reveal, input/selection) keep working; fog is player-perspective only.
- **The CSP `<meta>` is head-only by design** — it hardens the served file but is ignored inside a
  published Artifact (the platform wraps content in `<body>`). Safe in both; don't "fix" it by moving it.
- **Content-only on purpose** — keep all CSS/JS inline; any external request would break both the Artifact
  CSP and the self-host CSP.
- **Balance numbers are sim-tuned, not human-playtested.** A headless AI-vs-AI harness (attach an `AI` to
  the `'player'` slot, loop `G.update` to resolution) drove the current numbers (CC 520 HP, turret dmg 11,
  relay income 16/5, sudden-death at 240 s, etc.) to eliminate the symmetric-standoff stalemate. Still tune
  *feel* with the user — the harness is symmetric AI-vs-AI, the worst case, not real human play.

## Status & roadmap
`HANDOFF.md` is the living status doc: what's done and the pending roadmap. **Done:** the Match Setup screen
+ N-team FFA (#24), the 5-item gameplay-analysis pass (feel/veterancy, construction time, parts economy +
turret upgrades, FFA smarts + Relay), and a sim-tested balance pass. Next candidates: #18 smarter AI macro
(pairs with FFA), #16/#17 objectives & abilities.
