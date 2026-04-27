# Architecture

Deadline Survivors is a small local game, but the code is split by responsibility so new contributors can find the right place to work.

## Runtime Modules

| Module | Responsibility |
| --- | --- |
| `src/deadline_survivors/game.py` | Main loop, input handling, frame updates, collision rules, and drawing. |
| `src/deadline_survivors/content.py` | Tunable content: enemies, upgrades, phases, difficulties, achievements, skins, badges, and patch themes. |
| `src/deadline_survivors/models.py` | Small data models shared by content and runtime logic. |
| `src/deadline_survivors/state_factory.py` | Runtime dictionary factories for enemies, projectiles, hazards, and related state. |
| `src/deadline_survivors/combat.py` | Pure combat reward rules such as insight values, fix labels, and stat keys. |
| `src/deadline_survivors/encounters.py` | Pure encounter helpers such as phase-based enemy spawn pools. |
| `src/deadline_survivors/audio.py` | Procedural sound generation and playback. |
| `src/deadline_survivors/ui.py` | Small reusable drawing helpers. |
| `src/deadline_survivors/ui_screens.py` | Extracted screen drawing helpers that do not own game state. |
| `src/deadline_survivors/storage.py` | Local save loading, validation, and persistence. |
| `src/deadline_survivors/constants.py` | Window, color, and save-path constants. |

## Change Guidelines

- Put new enemies, upgrades, achievements, skins, or difficulty tuning in `content.py`.
- Put new persistent save fields behind validation in `storage.py`.
- Put pure reward, label, or stat mappings in `combat.py`.
- Put pure spawn-selection helpers in `encounters.py`.
- Keep platform-specific startup behavior in `game.py` or `run_game.py`, not in content modules.
- Keep runtime entity fields documented in `models.py`. If a dictionary is still used at runtime, give it a `TypedDict` shape first.
- Use small factory methods for repeated runtime dictionaries so field changes happen in one place.
- Keep screen drawing helpers stateless; they should receive the game object but not own gameplay state.
- Keep comments factual. Explain constraints, edge cases, or non-obvious decisions instead of restating the code.

## Quality Gates

- `ruff check src tests run_game.py`
- `mypy`
- `python3 -m compileall src run_game.py tests`
- `PYTHONPATH=src ./.venv/bin/python -m unittest discover -s tests`
- `SDL_VIDEODRIVER=dummy ./.venv/bin/python run_game.py --smoke-test`

## Current Refactoring Direction

`game.py` still owns most runtime behavior. That is acceptable for the current game size, but future work should split it gradually:

1. Continue moving pure rules out of `game.py` before touching stateful runtime behavior.
2. Add tests before extracting collision, enemy movement, boss behavior, or save migrations.
3. Split tests by responsibility as new modules appear.

Each step should preserve behavior first, then improve implementation. Gameplay changes should be separate commits from structural refactors.
