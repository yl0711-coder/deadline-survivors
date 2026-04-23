from __future__ import annotations

from pathlib import Path
import json

from .constants import SAVE_DIRNAME, SAVE_FILENAME


def save_path() -> Path:
    """Return the best writable save path for local high-score data."""
    candidates = [
        Path.home() / SAVE_DIRNAME,
        Path.cwd() / SAVE_DIRNAME,
    ]

    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        return root / SAVE_FILENAME

    return Path(SAVE_FILENAME)


def load_best_time() -> float:
    """Load the saved best survival time, falling back to zero on bad data."""
    path = save_path()
    if not path.exists():
        return 0.0

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0.0

    value = data.get("best_time", 0.0)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def save_best_time(best_time: float) -> None:
    """Persist best survival time without failing the game on write errors."""
    path = save_path()
    payload = {"best_time": round(float(best_time), 2)}
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        return
