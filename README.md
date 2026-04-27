# Deadline Survivors

A local single-player arcade survival game built with Python and `pygame-ce`.

You play as a backend engineer shipping patches while bugs, meetings, alerts, scope creep, deadlines, and production outages close in.

## Demo

![Deadline Survivors gameplay demo](assets/demo.gif)

## Screenshots

| Title | Gameplay |
| --- | --- |
| ![Title screen](assets/screenshots/title.png) | ![Gameplay](assets/screenshots/gameplay.png) |

| Upgrade | Game Over |
| --- | --- |
| ![Upgrade selection](assets/screenshots/upgrade.png) | ![Game over summary](assets/screenshots/game-over.png) |

## Play

Download a zip package from GitHub Releases:

- `deadline-survivors-windows.zip`
- `deadline-survivors-macos-intel.zip`
- `deadline-survivors-macos-apple-silicon.zip`
- `deadline-survivors-linux.zip`

Intel Macs should use the Intel package. Apple Silicon Macs should use the Apple Silicon package.

## Run From Source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run_game.py
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py run_game.py
```

## Controls

- `WASD` or arrow keys: move
- `Enter` / `Space`: confirm menu actions
- `1`, `2`, `3`: choose difficulty or level-up upgrades
- `A`: achievements
- `H`: local run history
- `B`: cycle badges
- `S`: cycle player skins
- `T`: cycle patch themes
- `P`: pause / resume
- `Esc`: close menus or quit

## Gameplay

- Keep moving to avoid enemies and deadline zones.
- Patches fire automatically at nearby threats.
- Collect insight shards to level up.
- Choose upgrades to shape the current run.
- Grab Coffee Breaks, Refactor Bombs, and CI Boosts when they drop.
- Capture Deploy Windows for bonus insight, healing, and Focus Mode.
- Build Momentum by moving; high Momentum improves patching and pickup flow.
- Prioritize Production Outages before they flood the map with hazards and support enemies.
- Review your last 10 completed runs locally with `H`.

## Project Notes

The game uses:

- `pygame-ce` for windowing, input, rendering, audio, and timing
- `PyInstaller` for Windows, macOS, and Linux packages
- GitHub Actions for tests, packaged binary smoke tests, and release zips
- `ruff` for lightweight linting

For details:

- [MANUAL.md](MANUAL.md): full player and maintainer guide
- [ARCHITECTURE.md](ARCHITECTURE.md): code structure and refactoring rules
- [README.zh-CN.md](README.zh-CN.md): Chinese README
