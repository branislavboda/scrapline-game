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
- Foundations: fog of war, camera + minimap, 3000×1900 world, persistent-debris economy, Silo supply
  cap (CC houses 30, +10/Silo), Turret defense.

## ROADMAP — what's left (the task list is NOT persisted across sessions; this is it)
**Next the user wanted (biggest):**
- **#24 — 4× map + up to 3 colored AI opponents (FFA).** The big refactor: generalize the 2-team
  ('player'/'enemy') + per-team-resource model to **N teams** (player + 1–3 AIs), each its own color,
  resources/parts/upg/queues, and AI instance; **free-for-all** targeting via `enemiesOf` (everyone
  not on your team); win = all enemy CCs gone, lose = your CC gone. Menu selector for AI count. World
  ~4× area (≈2× each dim → ~6000×3800) with bases placed around it. *Wide change — do it as its own
  carefully-verified pass; this is exactly where rushing reintroduces regressions.*

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
Confirm with the user: jump into **#24 (4× map + multi-AI)**, or do a quick playtest/tuning pass on the
current build first. Re-publish the Artifact once the tool is available so the hosted link isn't stale.
