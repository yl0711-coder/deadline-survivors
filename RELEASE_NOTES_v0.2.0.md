# Deadline Survivors v0.2.0

## Title

`v0.2.0 Playable Release`

## Summary

This release turns `Deadline Survivors` into a complete local playable desktop game with a cleaner game flow, clearer menus, better run reports, stronger boss / powerup rules, and automated release packaging.

Players can now download platform-specific zip packages from GitHub Releases, unzip them, and run the game without setting up Python.

## Download Packages

The release workflow builds three downloadable packages:

- `deadline-survivors-windows.zip`
- `deadline-survivors-macos.zip`
- `deadline-survivors-linux.zip`

Each package includes the runnable game binary plus:

- `README.md`
- `README.zh-CN.md`
- `MANUAL.md`

## Highlights

### Game Flow

- added a cleaner title menu with `Start Game`, `How To Play`, and `Game Story`
- added a scrollable help page for controls, upgrades, powerups, and core loop
- redesigned the game-over screen into a readable run report with next-action menu
- improved the achievements page layout and summary cards

### Gameplay

- refined `Refactor Bomb` into heavy screen-wide damage instead of unconditional enemy deletion
- bosses can survive `Refactor Bomb`, but low-health bosses can still be finished by it
- `Refactor Bomb` now only rewards enemies it actually defeats
- `Refactor Bomb` suppresses `Scope Creep` splitting so it behaves like a true panic clear
- unified resolved-pressure statistics across Bug, Meeting, Alert, Scope Creep, and Outage

### Balance And Feedback

- added clearer Easy / Medium / Hard difficulty labels
- added level-scaled powerups and upgrade gains so later runs feel more responsive
- added compact translucent HUD panels so gameplay remains visible
- added death burst feedback without leaving the game-over screen shaking
- improved title, game-over, and achievements visual hierarchy

### Packaging

- added a Release workflow for tagged releases
- `v*` tags now build Windows, macOS, and Linux zip packages
- Release assets are attached directly to GitHub Releases

### Stability

- expanded automated tests for rendering states, game-over effects, achievements, powerups, boss behavior, and resolved statistics
- verified source compile checks and headless tests
- verified PyInstaller packaging smoke test locally

## Controls

- `WASD` / arrow keys: move
- `Up` / `Down` on title: choose menu item
- `Enter` / `Space` on title: confirm menu item
- `1` `2` `3`: choose upgrades during level-up
- `1` `2` `3` on title / game-over: choose difficulty
- `Left` / `Right` on game-over: choose restart, achievements, or main menu
- `Enter` on game-over: confirm selected action
- `Space` on game-over: quick restart
- `A`: open achievements on title / game-over
- `B`: cycle unlocked badges
- `S`: cycle unlocked player skins
- `T`: cycle unlocked patch themes
- `P`: pause / resume
- `Esc`: quit or close help/story pages

## Suggested Release Text

`v0.2.0` is the first complete playable release of `Deadline Survivors`.

It includes a full local game loop, title/help/story menus, multiple enemy types, the `Production Outage` mini-boss, upgrades, temporary powerups, local achievements, cosmetic unlocks, run evaluation, and polished result screens.

This version also adds platform-specific GitHub Release packages for Windows, macOS, and Linux so players can download, unzip, and play without installing Python.
