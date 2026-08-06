# SCRAPLINE — v1.0 web release guide

The whole game is the single file `scrapline/index.html`. It is content-only (no
`<!doctype>/<html>/<head>/<body>`), but browsers render it standalone fine — the `<head>` tags at
the top (charset, viewport, CSP, title, favicon, OG) get hoisted automatically. **No build step.**

## Deploy to itch.io (free, fastest)

1. Rename/copy `index.html` → keep the filename **`index.html`**.
2. Zip it: `zip scrapline.zip index.html` (a single file in the zip root).
3. On itch.io → **Create new project** → Kind of project: **HTML**.
4. Upload `scrapline.zip`, tick **"This file will be played in the browser"**.
5. Embed settings: **Manually set size** ~1280×800, tick **Fullscreen button** and
   **Mobile friendly = off** (desktop-first v1.0).
6. Set the page copy from the section below. Publish as **Public** (or Restricted for a soft-launch).

Same file also works on Netlify/Cloudflare Pages/GitHub Pages — just drop `index.html` at the root.

## Store page copy (draft)

**Title:** SCRAPLINE

**Tagline (one line):** A neon RTS where every wreck reshapes the battlefield.

**Short description:**
> Command a scrapyard army in a fast, neon real-time strategy skirmish. Every destroyed unit leaves
> wreckage that blocks paths and can be scavenged for spare parts — so the battlefield literally
> rebuilds itself as you fight. Mine scrap, tech up, counter your enemy's army, seize the central
> Relay, and blow up their Command Center. Play free-for-all against 1–3 AI opponents.

**Features:**
- Persistent-debris economy — wrecks block pathing and are scavenged for parts (the hook).
- Counter triangle: Tank > Raider > Artillery > Tank, plus siege Artillery.
- Tech + upgrades that visibly reshape your tanks *and* turrets; units rank up (veterancy).
- Active abilities: Barrage / Repair Field / Recon Scan (Q/W/E).
- Free-for-all vs 1–3 colored AIs on a map that scales with player count; a capturable center Relay.
- A full Match Setup screen: game speed, economy, AI difficulty/count/aggression, fog, map layout.
- One self-contained file. Synth SFX + procedural music. No downloads, no accounts.

**Controls:** Drag-select · double-click = all combat units · right-click = move / attack / clear /
repair · select your Command Center + right-click = rally · **Q/W/E** abilities · **H/T/R/A/S** build ·
**1/2/F** structures · **3/4/5** upgrades · **B** overclock · arrows / screen-edge / minimap = pan ·
**P** pause · **Esc** cancel. First match shows a 5-step tutorial.

## Cross-browser test checklist (do this on your machine before public launch)

Run `python3 server.py` (or open the itch draft) and verify in **Chrome, Firefox, and Safari**:

- [ ] Loads with no console errors (DevTools → Console).
- [ ] Favicon shows in the tab.
- [ ] Audio starts after the first click (autoplay policy) — SFX + music; mute button works.
- [ ] First-run tutorial appears (clear site data / new profile to re-trigger), Skip works, and it
      does not reappear on the next match.
- [ ] Match Setup sliders/toggles work; settings persist across reload (localStorage).
- [ ] A full match plays start→finish: build, fight, abilities, win/lose screen, New Battle.
- [ ] Safari specifics: `webkitAudioContext` path works; no layout clipping of HUD; minimap correct.
- [ ] Resize the window mid-match — HUD + canvas stay correct.

## Known scope for v1.0 (intentional)

- **Desktop-first.** Touch/mobile controls are deferred (RTS-on-touch is its own project).
- **No multiplayer.** Skirmish vs AI only.
- **No match autosave/resume** (fragile for a real-time sim; low value). A refresh restarts the match.

## After launch — the point of all this

Get **30–50 real players** and watch one number: do they finish a match, and do they come back?
Post the link to r/RTS, r/WebGames, and an itch soft-launch. Features are done; **demand is the open
question** — that data decides whether multiplayer / Steam / more content is worth building.
