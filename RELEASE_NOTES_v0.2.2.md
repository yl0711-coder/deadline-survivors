# Deadline Survivors v0.2.2

`v0.2.2 macOS Intel Release Fix`

This patch fixes the macOS Intel release build.

## Fixed

- Build the Intel macOS package on GitHub Actions with `macos-15-intel`.
- Keep the Apple Silicon package separate as `deadline-survivors-macos-apple-silicon.zip`.
- Keep the Intel package separate as `deadline-survivors-macos-intel.zip`.

## Download Guide

- Intel Mac: download `deadline-survivors-macos-intel.zip`.
- Apple Silicon Mac, including M1 / M2 / M3 / M4: download `deadline-survivors-macos-apple-silicon.zip`.
- Windows: download `deadline-survivors-windows.zip`.
- Linux: download `deadline-survivors-linux.zip`.

The previous macOS package problem was caused by an architecture mismatch: an ARM64 binary cannot run on an Intel Mac and reports `bad CPU type in executable`.
