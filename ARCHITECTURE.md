# Architecture

Deadline Survivors is a local Python arcade game. The code is organized so each feature area has a clear owner, and a bug in one area can usually be fixed in the matching module instead of touching the full runtime.

## Startup Flow

The desktop launcher is intentionally thin:

1. `run_game.py` adds `src` to `sys.path` for local source runs.
2. `deadline_survivors.game.main()` is imported as the public entrypoint.
3. `deadline_survivors.game` keeps compatibility exports for tests and older imports.
4. `deadline_survivors.modules.runtime.Game` owns the main loop and composes the feature mixins.

`game.py` should stay small. New gameplay logic should not be added there.

## Runtime Modules

| Module | Responsibility |
| --- | --- |
| `src/deadline_survivors/game.py` | Public entrypoint and compatibility exports. Keep this file thin. |
| `src/deadline_survivors/modules/runtime.py` | Game lifecycle, pygame setup, frame orchestration, and top-level run finalization. |
| `src/deadline_survivors/modules/run_state.py` | Run-local state initialization: menus, player stats, combat defaults, directors, build state, feedback, stats, and runtime collections. |
| `src/deadline_survivors/modules/input.py` | Keyboard input, title menu, game-over menu, pause, help/about navigation, and level-up choice selection. |
| `src/deadline_survivors/modules/renderer.py` | World rendering, player/enemy drawing, HUD, visual effects, and shared text blitting. |
| `src/deadline_survivors/modules/overlay_renderer.py` | Non-world overlays: help, about, achievements, pause, level-up choices, and game-over report. |
| `src/deadline_survivors/modules/progression.py` | Cosmetics, upgrades, XP level choices, achievements, run evaluation, and progression persistence hooks. |
| `src/deadline_survivors/modules/combat_system.py` | Projectile firing, enemy contact, combat resolution, XP shard pickup, powerups, chain shots, overclock burst, failsafe, and enemy kill side effects. |
| `src/deadline_survivors/modules/director_system.py` | Encounter pressure: enemy spawning, crisis waves, boss spawning, hazards, and deploy-window objectives. |
| `src/deadline_survivors/modules/player_system.py` | Player movement, momentum tiers, regeneration, pulse/drone build effects, and floating text feedback. |
| `src/deadline_survivors/content.py` | Tunable content: enemy definitions, upgrades, phases, difficulties, achievements, skins, badges, and patch themes. |
| `src/deadline_survivors/models.py` | Shared dataclasses and `TypedDict` runtime state shapes. |
| `src/deadline_survivors/state_factory.py` | Factory functions for runtime dictionaries such as enemies, projectiles, hazards, and outage bosses. |
| `src/deadline_survivors/combat.py` | Pure combat mapping rules: fix labels, insight values, and stat keys. |
| `src/deadline_survivors/encounters.py` | Pure encounter helpers such as phase-based enemy spawn pools. |
| `src/deadline_survivors/audio.py` | Procedural sound generation and playback. |
| `src/deadline_survivors/ui.py` | Reusable drawing helpers. |
| `src/deadline_survivors/ui_screens.py` | Stateless title/menu scene helpers. |
| `src/deadline_survivors/storage.py` | Local save loading, validation, defaults, and persistence. |
| `src/deadline_survivors/constants.py` | Window, color, and save-path constants. |

## Where To Change Things

| Change | Start Here |
| --- | --- |
| Add or tune an enemy | `content.py`, then `director_system.py` only if spawn behavior changes. |
| Change enemy movement, boss behavior, hazards, or deploy windows | `modules/director_system.py`. |
| Change projectile behavior, powerups, enemy rewards, or contact damage | `modules/combat_system.py`. |
| Change upgrade effects, level-up choices, achievements, skins, badges, or run evaluation | `modules/progression.py`. |
| Change player movement, momentum, regeneration, pulse, drone, or floating text feedback | `modules/player_system.py`. |
| Change keyboard shortcuts or menu navigation | `modules/input.py`. |
| Change the HUD, player visuals, enemy visuals, or world effects | `modules/renderer.py`. |
| Change help/about, achievements, level-up, pause, or game-over screens | `modules/overlay_renderer.py`. |
| Change save data shape | `storage.py` plus tests for migration/default behavior. |
| Change startup, packaged binary entry, or smoke-test behavior | `run_game.py` or the thin `game.py` entrypoint. |
| Change initial run defaults or reset behavior | `modules/run_state.py`. |

## Design Rules

- Keep `game.py` as an entrypoint, not a feature module.
- Keep `runtime.py` focused on lifecycle and shared state coordination.
- Keep feature modules cohesive. If a bug says "powerup", the first file to inspect should be `combat_system.py`; if it says "achievement", inspect `progression.py`.
- Preserve public compatibility exports in `game.py` when tests or users import old symbols.
- Prefer behavior-preserving refactors in separate commits from gameplay changes.
- Do not move tuning constants into runtime code if they belong in `content.py`.
- Keep runtime dictionaries defined through `models.py` and `state_factory.py`; avoid ad-hoc dictionary shapes in multiple files.
- Add or update focused tests before changing risky systems such as enemy collisions, boss attacks, powerups, save data, or input handling.

## Quality Gates

Run these before committing structural changes:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy
.venv/bin/python -m compileall src run_game.py
SDL_VIDEODRIVER=dummy .venv/bin/python run_game.py --smoke-test
```

## Current Status

The original monolithic `game.py` has been reduced to a thin compatibility entrypoint. Runtime behavior is split across input, renderer, overlay-renderer, progression, combat, director, player-system, and run-state modules. `runtime.py` now stays focused on pygame lifecycle, frame orchestration, and run finalization.
