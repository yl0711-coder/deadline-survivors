# Deadline Survivors v0.2.5

`v0.2.5 Packaged Binary Smoke Tests`

This patch adds real startup smoke tests for packaged release binaries.

## Added

- Add `--smoke-test` to initialize the game and exit immediately.
- Run the packaged Linux executable in GitHub Actions after PyInstaller builds it.
- Run the packaged Windows executable in GitHub Actions after PyInstaller builds it.
- Run the packaged macOS app executable in GitHub Actions after PyInstaller builds it.

## Why

Source-level tests are useful, but they do not prove the packaged executable can start. This release verifies the built binary itself on each target platform before publishing the zip assets.
