# Deadline Survivors Manual

## Overview

`Deadline Survivors` is a local arcade survival game.

The design goal is:

- easy to start
- easy to distribute
- short sessions
- strong replay loop

## Player Manual

### Objective

Survive as long as possible while shipping patches, collecting insight, taking optional map objectives, and building a stronger developer.

### Title Menu

The title screen keeps the first view simple:

- `Start Game`: starts a run
- `How To Play`: opens a scrollable help page
- `Game Story`: opens a short theme and premise page

Use `Up` / `Down` to choose a menu item and `Enter` or `Space` to confirm it.

The help page can be scrolled with `Up` / `Down` and closed with `Esc`.

The title screen also shows a small preview scene with the developer, enemy pressure, and patch projectiles so the game premise is visible before the first run.

### Game Over Menu

The game-over screen is designed as a compact run report:

- survival time, best run, difficulty, and run evaluation are shown first
- four large cards summarize resolved pressure, insight, deploys, and powerups used
- `Left` / `Right` selects restart, achievements, or main menu
- `Enter` confirms the selected action
- `Space` restarts immediately

Detailed long-term progress is intentionally kept on the achievements page so the failure screen stays readable.

### Difficulty Selection

The title screen and retry screen support three difficulty presets:

- `Easy`: lower pressure and softer enemy stats
- `Medium`: baseline balance
- `Hard`: higher pressure, tougher enemies, and tighter pacing

Difficulty currently affects enemy HP, enemy damage, spawn pace, and insight gain.

### In-Run HUD

The combat HUD is deliberately compact and translucent.

- the left panel shows phase, time, level, difficulty, best time, HP, insight, and momentum
- the right side shows only active status effects and short controls
- the player can still be seen through the HUD if they move behind it

This keeps the screen readable without turning the HUD into a hard obstacle during play.

### Enemies

- `Bug`: basic chaser, common and persistent
- `Meeting`: larger and slower, higher pressure
- `Alert`: fast threat, punishes poor positioning
- `Scope Creep`: medium threat that appears later and creates crowd pressure

### Deadline Zones

Red deadline zones begin appearing after the early game.

- a warning ring appears first
- the active zone damages the player if they keep standing inside
- later levels spawn zones more frequently and with a wider radius

The intended counterplay is simple: do not camp the center. Keep rotating, collect insight on the move, and treat safe floor space as a resource.

### Deploy Windows

Deploy windows are optional green objectives that appear after the opening.

- reach the deploy area before the timer expires
- stay inside long enough to fill the progress circle
- completion grants bonus insight, a small heal, and temporary `Focus Mode`

The deploy is intentionally optional. If the screen is too crowded, skipping it can be correct. If you can safely rotate into it, completing it accelerates the run and gives a short power spike.

### Momentum And Focus

Momentum rewards active play.

- movement builds momentum
- standing still drains momentum
- momentum has visible `Flow` and `Overdrive` tiers
- higher tiers increase insight gain, pickup range, patch size, and patch speed
- `Overdrive` changes patch color so the state is visible without reading the HUD
- `Focus Mode` temporarily boosts the same loop after a successful deploy

The goal is to make movement valuable even when a strong build can kill normal enemies automatically.

### Leveling

When the insight bar fills, the game pauses and shows three upgrade choices.
Required insight increases after each level, so later levels take longer than early levels.
Level-up rewards are intended to be run-long build choices, not short temporary effects.

The current insight curve is:

- Level 1 to 2: 70 insight
- Level 2 to 3: 107 insight
- Level 3 to 4: 158 insight
- Level 4 to 5: 223 insight
- Level 5 to 6: 302 insight

The design intent is that early upgrades teach the build system, while later upgrades are spaced farther apart so the action flow is not interrupted too often.

Choose one with:

- `1`
- `2`
- `3`

Available upgrades:

- `Patch Notes`: higher patch damage
- `Coffee Rush`: higher movement speed
- `Multicast`: one more shipped patch, capped to avoid idle builds becoming too strong
- `Insight Radar`: wider insight pickup radius
- `Cache Shield`: higher max HP plus a small immediate recovery
- `Rollback Thread`: more patch pierce
- `Pager Burst`: periodic incident sweep damage
- `Quiet Hour`: slow passive recovery
- `Code Review`: patches chain into nearby issues
- `Pair Programmer`: an orbiting helper fires extra patches
- `Rollback Guard`: low HP triggers a defensive stabilization pulse
- `Overclocked Build`: Overdrive hits create a small burst around the target

### Powerups

Enemies can drop temporary powerups:

- `Coffee Break`: restores part of HP
- `Refactor Bomb`: deals heavy screen-wide damage, clears most regular enemies, and only rewards enemies it actually defeats
- `CI Boost`: temporarily speeds up automatic patching

These are intentionally separate from level-up choices. Powerups create recovery moments during action, while level-ups shape the build for the whole run.
Powerups and several upgrade gains scale slightly with level so later runs can become harder without making the player feel flat.

### Player Visuals

The player is rendered as a small developer character with simple procedural shapes instead of external image assets.

- The round head and small body make the player easier to track than a plain dot.
- The laptop shape supports the backend-engineer theme.
- The `</>` mark on the laptop helps communicate that the character is coding.
- The character leans slightly toward movement direction, which gives the controls more feedback.

This keeps the project lightweight while leaving room for future skins or sprite assets.

### End-Of-Run Report

When a run fails, the game shows a compact report with:

- a run evaluation title
- a short summary sentence
- one or two build tags
- newly unlocked local achievements, when applicable
- survival time
- selected difficulty
- total insight collected
- bugs fixed
- meetings dodged
- alerts silenced
- scope trimmed
- outages resolved
- deploy windows completed
- powerups used

Before the report settles, the player death location shows a short burst effect. This is a visual feedback effect only and does not keep the screen shaking after the run ends.

### Local Achievements

The current build includes a first batch of local achievements stored on disk.

- `First Patch Rush`
- `First Deploy`
- `First Outage`
- `Hard Survivor`
- `Deploy Addict`
- `Pair Flow`
- `Review Cascade`
- `Bug Tracker`

These are intentionally offline-first. They give repeat runs longer-term goals without requiring accounts or an online backend.

The achievements panel can be opened from the title or game-over screen with `A`, then closed with `A` or `Backspace`.

The panel groups achievements into milestone, challenge, build, and mastery sections so the list reads more like a progression page than a flat checklist.

Some achievements now unlock cosmetic player skins. These can be cycled with `S` on the title or game-over screen and are stored locally.
Achievements can also unlock lightweight badges. These can be cycled with `B` and are persisted locally in the same progression save.
Achievements can also unlock patch themes. These can be cycled with `T`, persist locally, and still inherit momentum color shifts during `Flow` and `Overdrive`.

### Pause And Moment-To-Moment Feedback

The run can now be paused with `P`.

The game also includes lightweight built-in feedback systems:

- procedural sound effects generated at runtime
- small screen shake for hits, bomb clears, pulse bursts, and crisis spikes
- pause overlay for longer sessions

These are intentionally small touches, but they make the game feel less like a prototype and more like a playable build.

### Pressure Phases

Runs move through several pressure phases:

- `Warmup`: lighter pressure and more room to stabilize
- `Incident Queue`: mixed waves begin
- `Alert Storm`: faster enemies appear more often
- `Deadline Crunch`: sustained late-run pressure

### Crisis Events

After roughly 55 seconds, the director can trigger crisis events near the player:

- `Standup Swarm`: many bugs and a blocker
- `Pager Storm`: fast alert enemies arrive together
- `Scope Review`: scope creep enemies pressure space and split on death

### Outage Mini-Boss

From the mid game onward, the run can spawn a `Production Outage` mini-boss.

- It prefers medium range instead of behaving like a normal chaser.
- It emits hazard waves, which reduces safe floor space.
- It summons support enemies, so ignoring it causes the screen to degrade.
- It has a dedicated HP bar and should become the primary target for most builds.

Elite enemies can appear later in a run. They are shown with an orange outline and are intentionally harder to clear.

### Common Strategies

- keep moving in arcs instead of straight lines
- leave red warning zones before they become active
- route toward deploy windows when the enemy wave gives you space
- grab Coffee Breaks before taking risky deploy windows
- save Refactor Bombs for crowded screens
- keep momentum up before collecting large insight drops
- collect insight in controlled loops, not blindly
- take movement speed early if you are getting cornered
- take Multicast or damage upgrades early if enemies pile up
- use CI Boost pickups for temporary patch speed instead of expecting it as a level-up
- recovery upgrades are best when you already have enough damage to stay alive
- pulse damage is strongest when the screen starts getting crowded
- piercing patches become much better once meetings and scope creep stack together
- Multicast improves coverage, but each extra patch reduces per-patch damage

## Maintainer Manual

## Gameplay Architecture

Most gameplay state lives in `Game` because this is still a compact single-file prototype.
The current separation is by update and draw responsibility:

- update methods mutate gameplay state, timers, collisions, and rewards
- draw methods render the current state without changing gameplay decisions
- title, help, about, achievements, playing, paused, level-up, and game-over are explicit screen states
- level-up upgrades are run-long build changes
- powerups are temporary or immediate effects
- deploy windows and momentum are optional risk-reward systems
- game-over effects use a small update path so short failure animations can finish after gameplay stops

If the project grows, the first worthwhile refactor would be moving enemies, powerups, and objectives into small modules while keeping the public game loop unchanged.

## Source Layout

```text
deadline-survivors/
├── .github/workflows/build.yml
├── MANUAL.md
├── README.md
├── README.zh-CN.md
├── requirements.txt
├── run_game.py
├── pyproject.toml
└── src/deadline_survivors/
    ├── __init__.py
    ├── constants.py
    ├── game.py
    └── storage.py
```

## Packaging Strategy

This project supports two distribution modes:

### 1. Source Code

Players install Python and dependencies, then run:

```bash
python3 run_game.py
```

### 2. Binary Distribution

Players download an already packaged binary for their OS.

Packaging uses `PyInstaller`.

For `src/` layout packaging, pass `--paths src`.

If the default PyInstaller cache directory is not writable, set:

```bash
PYINSTALLER_CONFIG_DIR=.pyinstaller
```

Because PyInstaller is platform-native, binaries must be built on each target OS.

On macOS, use `--onedir --windowed` to create a proper `.app` bundle. Do not use `--onefile --windowed` for the macOS app package.

This repository includes CI builds for:

- Windows
- Linux
- macOS

Tagged releases create platform-specific GitHub Release zip assets:

- `deadline-survivors-windows.zip`
- `deadline-survivors-macos-intel.zip`
- `deadline-survivors-macos-apple-silicon.zip`
- `deadline-survivors-linux.zip`

Use `macos-intel` for Intel Macs and `macos-apple-silicon` for M1 / M2 / M3 / M4 Macs. macOS zips contain `deadline-survivors.app`; Windows and Linux zips contain a standalone executable. Create and push a tag such as `v0.2.5` to publish these release assets.

The release workflow also starts each packaged binary with `--smoke-test` before uploading zip assets.

## Test Strategy

The project uses headless automated tests for the highest-risk runtime paths.

Current coverage includes:

- game initialization
- upgrade execution paths
- rendering in major game states
- short update loops
- level-up transitions
- enemy behavior checks
- crisis event spawning
- deadline zone spawning and damage
- deploy objective completion
- momentum reward scaling
- powerup pickup and effects
- Multicast diminishing returns

Run tests locally with:

```bash
PYTHONPATH=src ./.venv/bin/python -m unittest discover -s tests
```

## Save Data

The game stores a very small save file for high score tracking in the user's home directory.

This avoids extra services and keeps the game fully offline.

If the home directory is not writable, the game falls back to a local project-side save directory.

## Documentation Rule

When gameplay, controls, packaging, or project positioning changes:

- update `README.md`
- update `README.zh-CN.md`
- update `MANUAL.md`

in the same change.
