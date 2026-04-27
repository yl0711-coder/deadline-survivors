# Deadline Survivors v0.2.3

`v0.2.3 macOS App Bundle Fix`

This patch fixes the macOS `.app` package.

## Fixed

- Build macOS packages with PyInstaller `--onedir --windowed` so `deadline-survivors.app` is a complete app bundle.
- Keep Windows and Linux packages as standalone executable files.
- Keep separate Intel and Apple Silicon macOS downloads.

## Download Guide

- Intel Mac: download `deadline-survivors-macos-intel.zip` and open `deadline-survivors.app`.
- Apple Silicon Mac, including M1 / M2 / M3 / M4: download `deadline-survivors-macos-apple-silicon.zip` and open `deadline-survivors.app`.
- Windows: download `deadline-survivors-windows.zip`.
- Linux: download `deadline-survivors-linux.zip`.

The previous macOS `.app` could hang because it was generated with `--onefile --windowed`, a combination PyInstaller warns against for macOS app bundles.
