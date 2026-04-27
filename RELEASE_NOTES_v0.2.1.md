# Deadline Survivors v0.2.1

## Title

`v0.2.1 macOS Packaging Fix`

## Summary

This patch release fixes macOS binary distribution by publishing separate packages for Intel Macs and Apple Silicon Macs.

The original `v0.2.0` macOS package was built as an `arm64` binary, so Intel Macs could show:

- `bad CPU type in executable`
- `This Mac does not support this application`

## Download Packages

Choose the package that matches your machine:

- Windows: `deadline-survivors-windows.zip`
- macOS Intel: `deadline-survivors-macos-intel.zip`
- macOS Apple Silicon: `deadline-survivors-macos-apple-silicon.zip`
- Linux: `deadline-survivors-linux.zip`

## What Changed

- Release workflow now builds macOS Intel packages on `macos-13`.
- Release workflow still builds Apple Silicon packages on `macos-latest`.
- Documentation now explains which macOS zip package to download.

## Notes

This release does not change gameplay. It only fixes the release packaging matrix and version metadata.
