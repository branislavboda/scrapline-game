# SCRAPLINE ⚡

A neon, top-down **real-time strategy** game where *every wreck reshapes the battlefield*. It's a single
self-contained HTML file — no build, no dependencies, no backend.

> Destroy the enemy Command Center. Scavenge the debris of battle for **scrap + spare parts**, repair your
> army, tech up, and out-maneuver the AI.

## Play

- **Locally:** `python3 server.py`, then open **http://localhost:4180** — or just open `index.html` in any
  modern browser.
- Everything (art, audio, logic) is inline in `index.html`; the audio is synthesized with Web Audio and all
  graphics are Canvas vector.

## Features

- **Fog of war** over a large scrolling world, with a **minimap** and camera (arrow keys / screen-edge / minimap).
- **Persistent-debris economy** — destroyed units leave burning wreckage and debris that **block
  pathfinding**; scavengers clear it for **scrap + spare parts** and repair units *and* buildings.
- **Counter-based roster** — **Tank ▸ Raider ▸ Artillery ▸ Tank**; Artillery has a **siege mode** (deploy
  for 2× range & damage).
- **Tech & economy** — a **Foundry** unlocks Artillery; **Silos** raise your unit cap; resource nodes have
  **5 richness levels** (click to inspect remaining) and a fresh node appears **every 5 minutes**.
- **Timed production** with a spare-parts **overclock**, plus a **tank-upgrade research** queue (range /
  armor / firepower).
- **Turrets** for base defense, three **difficulty** levels, pause, and an end-of-match stats screen.

## Controls

- **Drag** to box-select · **double-click** selects all combat units · **right-click** to move / attack /
  clear debris / repair.
- **Arrows** / screen-edge / minimap to scroll · **Esc** cancel · **P** pause.
- Build units: **H** Harvester · **T** Tank · **R** Raider · **A** Artillery · **S** Scavenger · **B** overclock.
- Select your **Command Center** to build **Turret / Silo / Foundry** and research tank upgrades.

## Repo layout

| File | Purpose |
|---|---|
| `index.html` | The entire game (single file). |
| `server.py` | Tiny localhost static server (port 4180). |
| `CLAUDE.md` | Architecture, gotchas, and dev/verify workflow (for working on it with Claude Code). |
| `HANDOFF.md` | Current status + roadmap — what to build next. |
| `docs/PLAN.md` | The productionization plan. |

Built with [Claude Code](https://claude.com/claude-code).
