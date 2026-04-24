# Deadline Survivors v0.1.2

## Title

`v0.1.2 Progression Update`

## Summary

This release turns `Deadline Survivors` from a simple playable prototype into a more complete repeat-play local game.

The biggest change is long-term progression:

- end-of-run evaluation titles
- local achievements
- an achievements panel
- achievement-based cosmetic skins
- achievement-based badges

It also adds stronger mid-game pressure and better run feedback with a dedicated `Outage` mini-boss, pause support, built-in procedural audio, and improved result screens.

## Highlights

### Progression

- added run evaluation titles and build-style summaries on the result screen
- added local achievements stored on disk
- added an achievements panel that can be opened from title / game-over with `A`
- added grouped achievement presentation:
  - `Milestones`
  - `Challenges`
  - `Build Goals`
  - `Mastery`
- added progress text, completion rate, next-target hint, and recent unlock highlighting

### Cosmetic Rewards

- achievements now unlock cosmetic player skins
- skins can be cycled with `S` on title / game-over
- selected skin is stored locally
- achievements now also unlock lightweight badges
- badges can be cycled with `B` on title / game-over
- selected badge is stored locally

### Gameplay

- added `Production Outage` mini-boss encounters
- `Outage` uses hazard waves, support summons, and a dedicated boss HP bar
- added more build-defining upgrades:
  - `Code Review`
  - `Pair Programmer`
  - `Rollback Guard`
  - `Overclocked Build`
- improved end-of-run feedback so each run feels more distinct

### Feel And Presentation

- added pause / resume with `P`
- added procedural runtime-generated sound effects
- added light screen shake for impacts and pressure spikes
- improved title and game-over screens with clearer progression hooks

### Stability

- fixed Windows CI environment handling
- expanded automated tests for progression, achievements, mini-bosses, cosmetics, and rendering states

## Controls

- `WASD` / arrow keys: move
- `Space`: start / continue
- `1` `2` `3`: choose upgrades
- `1` `2` `3` on title / game-over: choose difficulty
- `A`: open achievements
- `B`: cycle unlocked badges
- `S`: cycle unlocked skins
- `P`: pause / resume
- `Esc`: quit

## Suggested Release Text

`v0.1.2` focuses on progression and replay value.

This update adds local achievements, a dedicated achievements panel, run-evaluation titles, and cosmetic unlocks including skins and badges. It also introduces the `Production Outage` mini-boss and several more build-defining upgrades so mid-game runs feel more structured and varied.

The game remains fully local and offline-friendly: progression, cosmetics, and best-time data are stored on disk without requiring any online account.

