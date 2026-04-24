# Deadline Survivors

A local single-player action game built with Python and `pygame-ce`.

You play as a backend engineer trying to survive waves of:

- Bugs
- Meetings
- Alerts
- Scope creep

The game is designed for local play only:

- clone from GitHub
- run from source
- or download a packaged binary for your OS

## Why This Stack

This project uses two mature open-source components:

- `pygame-ce` for the game window, input, rendering, audio, and timing
- `PyInstaller` for packaging distributable binaries

This keeps the game simple to develop, easy to modify, and practical to distribute.

## Run From Source

1. Create a virtual environment.
2. Install dependencies.
3. Start the game from the terminal.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run_game.py
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py run_game.py
```

## Package Binaries

The repository supports packaging with `PyInstaller`.

```bash
PYINSTALLER_CONFIG_DIR=.pyinstaller \
pyinstaller --noconfirm --clean --paths src --onefile --windowed --name deadline-survivors run_game.py
```

Important:

- `PyInstaller` is not a cross-compiler.
- Windows binaries must be built on Windows.
- macOS binaries must be built on macOS.
- Linux binaries must be built on Linux.
- On restricted environments, set `PYINSTALLER_CONFIG_DIR` to a writable local directory.

This repository includes a GitHub Actions workflow that builds artifacts on:

- Windows
- Linux
- macOS

## Controls

- `WASD` or arrow keys: move
- `Space`: start / continue
- `1`, `2`, `3`: choose upgrades during level-up
- `1`, `2`, `3` on title / game over: choose difficulty
- `A`: open achievements on title / game over
- `S`: cycle unlocked player skins on title / game over
- `P`: pause / resume
- `Esc`: quit

## Gameplay Loop

- keep moving to avoid enemies and red deadline zones
- ship patches automatically
- collect dropped insight shards
- grab Coffee Breaks, Refactor Bombs, and CI Boosts
- capture optional deploy windows for burst rewards
- keep momentum high for better insight and faster patching
- prioritize `Outage` mini-bosses before they flood the screen with extra pressure
- level up and choose upgrades
- survive as long as possible
- adapt to changing pressure phases during the run

## Deploy Windows And Momentum

The game is not intended to be a pure idle shooter. After the opening, optional `Deploy Window` objectives appear on the map:

- enter the green deploy circle before it expires
- hold the area long enough to complete the deploy
- successful deploys grant bonus insight, a small heal, and temporary `Focus Mode`

`Momentum` rewards active movement:

- moving builds momentum
- standing still drains it
- higher momentum moves through `Flow` and `Overdrive` tiers
- `Flow` and `Overdrive` increase insight gain, pickup range, patch size, and patch rate
- `Overdrive` changes patch color, making the power spike visible during play
- `Focus Mode` gives a short burst that makes successful deploys feel valuable

This creates a risk-reward loop: chase the objective for faster growth, or ignore it when the screen is too dangerous.

## Level-Up Upgrades

Level-up choices are run-long build upgrades. Required insight increases after each level, so each shard becomes a smaller percentage of the bar over time.

Current insight requirement curve:

- Level 1 to 2: 70 insight
- Level 2 to 3: 107 insight
- Level 3 to 4: 158 insight
- Level 4 to 5: 223 insight
- Level 5 to 6: 302 insight

The curve keeps early progress readable, then slows down frequent upgrade interruptions during longer runs.

- `Patch Notes`: increases patch damage.
- `Coffee Rush`: increases movement speed.
- `Multicast`: ships one extra patch, up to the patch cap.
- `Insight Radar`: increases insight pickup range.
- `Cache Shield`: increases max HP and restores a small amount of HP.
- `Rollback Thread`: lets patches pierce one extra issue.
- `Pager Burst`: unlocks and improves periodic incident sweep damage.
- `Quiet Hour`: unlocks and improves slow automatic recovery.
- `Code Review`: chained patches bounce into nearby issues after a hit.
- `Pair Programmer`: adds an orbiting helper that fires extra patches.
- `Rollback Guard`: low HP triggers an emergency stabilizing pulse.
- `Overclocked Build`: Overdrive hits create small burst damage.

Short-term rescue effects are still handled by powerups, but the upgrade pool now also includes more build-defining mechanics so runs diverge more clearly.

## Powerups

Enemies can drop temporary powerups:

- `Coffee Break`: restores part of your HP, not a full heal
- `Refactor Bomb`: clears enemies on screen and drops small insight shards
- `CI Boost`: temporarily reduces patch cooldown

This keeps level-up choices focused on long-term build direction while powerups create quick, exciting recovery moments.

## Difficulty Modes

The title screen and retry screen now support three difficulty presets:

- `Casual`: softer pressure and more forgiving enemy stats
- `Normal`: the default intended balance
- `Crunch`: faster waves and harsher production pain

Difficulty affects enemy durability, enemy damage, spawn pace, and insight gain.

## Player Character

The player is drawn as a small developer character instead of a plain dot:

- head and body for clearer identity
- laptop shape to match the backend-engineer theme
- simple `</>` mark on the laptop screen
- slight movement lean so direction changes feel more alive

The style is intentionally simple because the project has no external art assets.

Unlocked achievements can now also open cosmetic player skins. Skin selection is local, persists on disk, and can be cycled from the title or game-over screen with `S`.

## End-Of-Run Stats

When a run ends, the game now shows a small production report:

- a run evaluation title
- a short build-style summary
- highlighted run tags
- any newly unlocked local achievements for that run
- total insight collected
- bugs fixed
- meetings dodged
- alerts silenced
- scope trimmed
- outages resolved
- deploy windows completed
- powerups used
- run difficulty

## Local Achievements

The game now tracks a first batch of local achievements without any online account:

- `First Patch Rush`: reach `Overdrive` for the first time
- `First Deploy`: complete a deploy window for the first time
- `First Outage`: defeat a `Production Outage`
- `Crunch Survivor`: survive 10 minutes on `Crunch`
- `Deploy Addict`: complete 5 deploys in one run
- `Pair Flow`: reach 2 `Pair Programmer` helpers
- `Review Cascade`: chain through 3 targets
- `Bug Tracker`: fix 500 bugs across runs

These are stored locally together with best-time data and are intended to add long-term goals before online systems exist.

The achievements panel now groups them into milestone, challenge, build, and mastery sections, and shows lightweight progress text for the longer goals.
It also shows a `Next target` hint so the player can immediately see the closest unfinished goal.

## Feedback Polish

The game now includes lightweight built-in feedback without external assets:

- procedural sound effects for patching, pickups, damage, level-ups, crisis events, pause, and failure
- light screen shake on hits, bombs, pulse bursts, and crisis spikes
- a pause overlay so longer runs are easier to manage
- a dedicated `Outage` HP bar and encounter banner for mini-boss moments

## Pressure Phases

Runs now move through light phase changes instead of using a flat spawn curve:

- `Warmup`
- `Incident Queue`
- `Alert Storm`
- `Deadline Crunch`

This gives the first minute more breathing room and makes later waves feel more distinct.

## Crisis Events

After the gentler opening phase, the game periodically triggers crisis events near the player:

- `Standup Swarm`: a dense group of bugs and a meeting blocker
- `Pager Storm`: several fast alert enemies
- `Scope Review`: scope creep pressure with split enemies

## Outage Mini-Boss

After the run settles into the mid game, a `Production Outage` mini-boss can appear:

- it keeps medium distance instead of simply rushing the player
- it emits hazard waves that cut safe floor space into smaller pockets
- it periodically summons support enemies, forcing a target-priority decision
- it has a dedicated boss HP bar so the run gains a clear combat objective

Later runs can also spawn elite enemies with an orange outline. They are tougher and prevent high-level builds from becoming idle.

## Deadline Zones

Mid-run and late-run pressure now includes red deadline zones that appear near the player's current position:

- warning rings appear before the zone becomes active
- active zones damage the player once if they keep standing inside
- the timer gets shorter as level and phase pressure increase

This is the main anti-idle mechanic. A strong Multicast build can clear enemies faster, but it cannot safely stand in one place forever.

## Balance Notes

Multicast is strong, but it now has diminishing returns:

- extra patches are capped
- high patch counts significantly reduce per-patch damage
- after the cap, Multicast improves patch rate and damage instead of adding infinite patches

## Manual

For a full player and maintainer guide, see:

- [MANUAL.md](MANUAL.md)
- [README.zh-CN.md](README.zh-CN.md)
