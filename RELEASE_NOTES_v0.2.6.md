# Deadline Survivors v0.2.6

`v0.2.6 Local History And Options`

This patch adds offline player-facing quality-of-life features and continues the internal module cleanup.

## Added

- Add a local `Run History` page opened with `H`.
- Store the latest 10 completed runs locally.
- Show the best local run, recent run times, difficulty, level, resolved pressure, and build tags.
- Add an `Options` page opened with `O`.
- Add sound effect and floating text toggles.
- Add clear-local-data confirmation for resetting local progress on the current computer.

## Changed

- Save data now merges older saves with default settings and empty run history.
- Powerup behavior is now isolated in `powerup_system.py` for easier maintenance.

## Verification

- Source tests, lint, type checks, compile checks, and headless smoke test passed locally.
- Packaged binary smoke tests run in GitHub Actions before Release assets are uploaded.
