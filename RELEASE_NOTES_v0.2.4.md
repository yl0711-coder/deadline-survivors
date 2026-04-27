# Deadline Survivors v0.2.4

`v0.2.4 Windows Startup Fix`

This patch fixes a Windows startup crash in the packaged executable.

## Fixed

- Stop using `pygame.font.SysFont()` during startup.
- Use pygame's bundled default font instead of querying the platform font registry.
- Add a regression test for startup when system font lookup is broken.

The previous Windows build could fail with:

```text
TypeError: expected str, bytes or os.PathLike object, not int
```

The failure happened while pygame was enumerating Windows system fonts.
