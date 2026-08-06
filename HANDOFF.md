# SCRAPLINE — continuation handoff

Read this together with the repo-wide **`/CLAUDE.md`** (its "SCRAPLINE architecture / gotchas /
preview & verification" sections are the technical map). This file is the *status + roadmap +
decisions* so a fresh session can continue without re-deriving anything.

## What it is
A polished single-file HTML5 Canvas RTS: `scrapline/index.html` (~1,015 lines, content-only — no
doctype/html/head/body — so it doubles as a Claude Artifact). One global `G` (a `Game`, created only
in `startGame`) owns the whole sim. No build, no modules, no external requests.

## Design north star (decided with the user)
Make it a **rich, StarCraft-like strategy game** — army composition, tech, map control, smart macro AI.
**NOT** an arcade/survival score-chase (the user explicitly rejected survival mode + veterancy).
"It ends too soon / too simple" was the complaint; the fix is depth + a real match arc.

## Source of truth & delivery
- **On-disk `scrapline/index.html` is authoritative.** Always edit + verify that.
- Hosted Artifact (default-private): https://claude.ai/code/artifact/7eb08a68-f7dc-4441-afeb-f817151ec918
  — **likely STALE.** The publish/Artifact tool was unavailable for the last several builds (restart
  fix, upgrade queue, roster/counters/tech, siege/scavenger/nodes never got republished). Re-publish
  to that same link when the tool is available again.

## How to run / verify (see CLAUDE.md for full detail)
- Human run: `python3 scrapline/server.py` → http://localhost:4180 (or open index.html).
- Claude preview MCP: the sandbox **can't read `~/Desktop`** (macOS TCC) and `python3 -m http.server`
  fails (os.getcwd blocked). Workaround: copy `index.html` into the session **scratchpad** dir and
  serve with a `__file__`-based `server.py`; point `.claude/launch.json`'s `scrapline` entry there.
  **That scratchpad path is session-specific — recreate the copy + repoint it each session.**
- Verify loop: `preview_start` → reload → `preview_console_logs level=error` (must be empty) →
  deterministic `preview_eval` sims (`G=new Game(diff)`; loop `G.update(1/60)`; assert invariants) →
  `preview_screenshot` desktop + `preview_resize` mobile. Viewport sometimes loads 0–1px → `resize()` first.

## DONE this session (all verified, no console errors)
- **Home screen + onboarding**: title, win condition, controls legend; **Mode** (Vs AI; "2-Player ·
  2 devices — coming soon" disabled) and **Difficulty** (Easy/Normal/Hard via the `DIFF` table).
- **App state machine** `appState ∈ {menu,playing,paused,over}` (drives `document.body.className`),
  **pause** (P / button), **end-of-match stats**, **audio mute** (master gain, persisted),
  **responsive HUD**, **security** (head-only CSP, guarded localStorage, OG/meta tags).
- **Timed production**: unit build queue + parts-fueled **overclock** (`G.queue`, `G.boost`); separate
  **tank-upgrade research queue** (`G.upgQueue`, escalating cost via `upgCommitted`).
- **Combat roster + hard counters**: `CombatUnit` → `Tank`/`Raider`/`Artillery`; `e.cls` ×
  attacker `bonusVs` in `G.damage` → **Tank > Raider > Artillery > Tank**; Artillery `splash` +
  **auto siege mode** (idle ~1s → 2× range/damage, deployed visual).
- **Foundry** tech building gates Artillery (`hasTech(team)`); built from the CC BUILD cluster.
- **Scavenger robustness**: no more chaotic spin (throttled `repathCd` + `_working` hysteresis +
  give-up timer), searches the whole map, repairs **buildings** as well as units.
- **Resource nodes**: 5 richness levels (`NODE_MAX`), 5-crystal gauge, **click to inspect** remaining
  (`nd._show`); a **new node every 5 min** (`spawnNode()` / `G.nextNode`) with a cue + minimap reveal.
- **Fixed the auto-restart bug**: `startGame`/restart gated on `appState` (+600ms debounce); restart
  only from `over`, start only from `menu`. **Keep these guards** (see CLAUDE.md gotcha — bit twice).
- Foundations: fog of war, camera + minimap, 6000×3800 world, persistent-debris economy, Silo supply
  cap (base 30, +10/Silo), Turret defense.
- **Match Setup screen + multi-AI FFA (#24 — DONE).** Dedicated pre-game `#setup` screen (appState
  `settings`, reached from the menu's "SET UP MATCH ▸") driven by a central **`CFG`** object
  (persisted to `localStorage` `scrapline.cfg`). Exposes game speed, starting scrap/parts (player+AI),
  node richness, AI difficulty preset + **1–3 opponents** + aggression/economy overrides, supply cap,
  start army, **fog on/off**, base placement (symmetric/random), and resource-node count. The sim is
  now **N-team**: per-team keyed state (`res`/`parts`/`upg`/`upgQueue` maps over `G.teams`),
  `enemiesOf` = everyone-not-you (true FFA, AIs fight each other), one `AI` per AI team targeting the
  nearest rival CC, per-team colors (`TEAM_COL`/`TEAM_DARK`: player cyan, ai1 red, ai2 orange,
  ai3 purple), win = all rival CCs gone / lose = player CC gone. World grew to 6000×3800 with bases on
  an ellipse ring via `layoutMap()`. *Balance across 2–4 players is unplaytested — tune with the user.*
- **Gameplay-analysis pass (5 improvements — DONE).**
  - **Feel fixes:** `separate()` is now velocity-based (dt-scaled, capped, wall-aware) — no more on-screen
    shoving or wall-clipping. **Veterancy**: `Shell` carries its `owner`; `G.damage(...,attacker)` credits
    kills → `G.promote()` (2/5/9 kills → vet 1/2/3, +15% hp & +12% dmg each, `baseDmg` bumped for Artillery
    so siege recompute sticks). Veterans draw gold chevrons + size scale (`vscale()`).
  - **Upgrade recognizability:** tank/turret `draw()` now reflect research — **range**=longer barrel,
    **power**=thicker/brighter barrel + white tip, **armor**=extra plating + size — plus the veterancy scale.
  - **Building construction time:** structures placed via `placeStructureAt` start `built=false` at 15% HP,
    ramp over 6–12 s with an animated progress ring + countdown, are attackable, and are inert until done
    (`popCap`/`hasTech` ignore unbuilt; turrets don't fire). Handled centrally in the `update` building loop.
  - **Parts as a 2nd currency:** shared `UNIT_COST/UNIT_TIME/UNIT_PARTS` + `STRUCT_COST/STRUCT_PARTS` tables;
    Artillery (+40◆), Foundry (+40◆), Turret/Silo (+15◆) cost parts too (player + AI pay). **Turrets now
    upgrade**: range/power derive live from `G.upg[team]`, armor bumps turret maxhp in `completeUpg` + at placement.
  - **FFA smarts + map control:** AI `pickTargetCC` is now scored (weakest + closest + **retaliate** via
    `G.threat[team]` set in `damage` + **anti-gang** crowding penalty via `ai.targetTeam`). A capturable
    center **Relay** (`G.relays`, `updateRelays`) grants the uncontested holder scrap/parts income + vision;
    drawn in-world + on the minimap.
- **Balance pass (sim-tested — DONE).** Ran a headless AI-vs-AI harness (attach an `AI` to the `'player'`
  slot so all teams are AI-driven; loop `G.update` to resolution) measuring win/timeout rates, duration,
  parts curves, tech-reach. **Finding:** symmetric defensive standoff — attacks bounced off tanky CCs and
  the debris-refuel economy sustained endless attrition → **65–75% of matches never resolved**, and
  scavenged parts inflated to ~650. **Tuning applied:** CC HP 1000→**520**; Turret dmg 14→**11**; scavenger
  parts yield ~halved (`clearClutter`: debris 4→2, wreckage `value*2`→`value*1.1`); AI standing-army cap
  `wave+2`→**+4** and waves now **focus-fire the target CC** (`attackTarget=tcc`) with a **33% chance to
  seize the Relay** instead; AI siege preference 0.3→**0.45**; **Relay income 8/3 → 16/5 per s** (strong
  enough to snowball and break ties); and a **"scrapline collapse" sudden-death** (`SUDDEN_T=240`) that
  decays all CCs after 4 min so nothing stalemates. **Result:** timeout **0%** across 1v1 / 4-team normal /
  4-team hard; match length ≈ 86 s (hard) to ≈ 300 s (stalemate-prone 1v1, caught by collapse); parts peak
  ~150–280. *Still first-pass vs a human — the harness is symmetric AI-vs-AI, the worst case for stalemates.*
- **Active abilities (#17 — DONE).** Player-only, parts-fueled, cooldown, click-to-target (arm via button or
  Q/W/E → click map; right-click/Esc cancels; `G.aiming` mirrors the `G.placing` flow). `ABILITIES` config +
  `G.abilityCd`/`G.effects`. **Barrage** (60◆/35s): ~9 explosions over 2 s in a radius, splash dmg + bonus vs
  buildings (base-cracker). **Repair Field** (45◆/30s): instant 45%-maxhp heal to allies in radius. **Recon
  Scan** (15◆/22s): reveals fog around a point ~6 s (ping in `updateFog`). HUD `#abilities` cluster (top-left)
  with cooldown veil + cost; `updateEffects(dt)` ticks strikes. Also a strong late-game parts sink.
- **Game-feel pass (StarCraft-fun — DONE).** Web-researched (pacing / attack-move / juice). **Root cause of
  "plays badly": the map was so large a Tank took ~107 s to cross and an attack ~95 s to arrive** (dead time).
  Fixes: **world size is now dynamic** (`let WORLD_W/H`, set per-match in the `Game` ctor by team count —
  3400×2200 / 4200×2800 / 5000×3300, all far tighter than the old 6000×3800); **unit speeds +~30%** (Tank
  56→74, Raider 112→146, Artillery 38→50, Harvester 52→66, Scavenger 66→84); **default `CFG.speed` 1.0→1.25**;
  `layoutMap` node offsets are now proportional to map size. **Attack-move feel:** `CombatUnit.update` now
  **stops to fight** any target in range (armies clash instead of milling); AI waves attack-move through
  defenders. **Rally point:** select a player CC → right-click sets `cc.rally`; `spawn()` sends new units there
  (dashed marker). **Result:** attack arrives in ~30 s; 1v1 resolves through real combat (~200 s, no more
  permanent stalemate); hard 1v1 median ~104 s; difficulty gradient intact (player-slot win ~83% normal → ~29%
  hard). Legend updated with ability + rally controls.
- **v1.0 web-polish (IN PROGRESS).** Path chosen: ship a free, single-player **web** v1.0 (no multiplayer).
  Done so far: **first-run onboarding coach** (`#tut`, 5 steps gated on player actions, Skip, persists via
  `localStorage scrapline.onboarded`; driven by `tutTick()` in `syncHUD`); **procedural synthwave music bed**
  (in `Audio2`: `musicSet`/`musicTick` lookahead scheduler, `CHORDS` Am-F-C-G, under the master mute; starts
  on `appState==='playing'` from `loop()`). Perf measured OK (~178 units = 2.3 ms/update) → not a v1.0 blocker.
  **Juice/polish (done):** screenshake is now **distance-attenuated** (`shake(a,x,y)` scales by distance to the
  camera view — off-screen deaths no longer jolt) and softened (explosion 0.5→0.34, breakdown 0.18→0.12);
  **selection feedback** (soft `Audio2.select()` blip + ring pop on drag/click/double-click select).
  Packaging done: data-URI favicon + `docs/RELEASE.md` (itch steps, page copy, cross-browser checklist).
  **Deferred:** full match autosave/resume (fragile + low-value for a real-time sim); touch/mobile
  (desktop-first v1.0). *Note: pre-mortem said the real risk is demand, not features — soft-launch early.*
- **Neon-holo graphics pass (chosen direction).** Self-contained Canvas-2D post-processing in `postFX()`
  (called in `render()` after the world, before HUD): **bloom** (downsampled high-contrast bright-pass →
  two additive blurred halos — threshold-style so it glows edges without washing out silhouettes), **CRT
  scanlines**, and a **cyan/magenta soft-light color grade**. `FX_OFF` try/catch fallback. `drawBackground`
  is now a **holographic floor** (faint minor grid + brighter pulsing major grid + a sweeping scan line +
  glowing border). **Ground contact shadows** under all entities in `render()` for depth. Keeps single-file /
  CSP (no WebGL, no assets). *Pending (user picked it too): a proper unit/building silhouette redraw — the new
  lighting already lifts the existing shapes, so that's an optional iterative art pass.* A full WebGL HDR
  pipeline (chromatic aberration, FXAA, tighter bloom) is the future ceiling if more fidelity is wanted.

**Remaining depth (the "more strategy" set):**
- #16 Capturable map objectives (refineries/relays → income/vision/parts; map control).
- #17 Active abilities (artillery barrage, scavenger overcharge, repair burst, recon ping).
- #18 Layered enemy defense + smarter AI macro (AI expands/techs/composes; fortified base/outposts).
- #19 Run variety + modifiers (randomized layout; scrap-rich / debris-storm / elite-AI).

**Productionization backlog (from the approved plan):**
- #6 Autosave + resume (localStorage, guarded JSON.parse, versioned — survive a refresh).
- #10 Performance pass (spatial hash + kill per-frame `enemiesOf()` allocations; O(n²) `separate()`).
- #11 Match-feel polish (rally points, cancel-queued-unit refund, control groups — note 1–5 keys are
  taken by build/upgrade, so rebind).
- #12 Touch / mobile controls (largest UX pass; also owns the mobile in-game HUD rework — the CC menu
  currently crowds the bottom bar on phones).
- #13 Cross-browser pass + (optional) Python concat build to keep single-file + a documented smoke test.

Approved plan with fuller detail: `~/.claude/plans/make-these-suggestions-into-wiggly-kettle.md`.

## Watch-outs when editing combat
- **`instanceof CombatUnit` vs `instanceof Tank`**: tank *upgrades* (`applyAllUpg`/`buyUpgrade`) are
  **Tank-only**; right-click attack orders, double-click-select, and the AI "army" use **CombatUnit**.
- Balance numbers (costs/HP/counter multipliers/build times) are a **first pass, not human-playtested** —
  a real playtest/tuning pass is still owed. Ask the user how it *feels* before deep balance work.

## Suggested first move in the new session
With **#24 done**, the highest-value next step is a **playtest/tuning pass** on 2–4-player FFA (AI
`DIFF` numbers, the new aggression/economy sliders, node/base spacing on the bigger map) — ask the user
how it *feels* first. Then pick from the depth set (#18 smarter AI macro pairs well with FFA). Re-publish
the Artifact once the tool is available so the hosted link isn't stale.
