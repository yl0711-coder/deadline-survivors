from __future__ import annotations

from pathlib import Path
import copy
import json

from .constants import SAVE_DIRNAME, SAVE_FILENAME


DEFAULT_PROGRESS_TOTALS = {
    "bugs_fixed": 0,
    "meetings_dodged": 0,
    "alerts_silenced": 0,
    "scope_trimmed": 0,
    "outages_resolved": 0,
    "deploys": 0,
    "runs_played": 0,
    "best_time": 0.0,
}

DEFAULT_ACHIEVEMENTS = {
    "first_overdrive": {"unlocked": False},
    "first_deploy": {"unlocked": False},
    "first_outage": {"unlocked": False},
    "crunch_survivor": {"unlocked": False},
    "deploy_addict": {"unlocked": False},
    "pair_flow": {"unlocked": False},
    "review_cascade": {"unlocked": False},
    "bug_tracker": {"unlocked": False},
}


def save_path() -> Path:
    """Return the best writable save path for local game and progression data."""
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


def default_progression() -> dict:
    """Return a fresh progression payload for achievements and cumulative stats."""
    return {
        "selected_skin": "default",
        "achievements": copy.deepcopy(DEFAULT_ACHIEVEMENTS),
        "totals": copy.deepcopy(DEFAULT_PROGRESS_TOTALS),
    }


def load_save_data() -> dict:
    """Load the raw save payload, tolerating older best-time-only files."""
    path = save_path()
    if not path.exists():
        return {"best_time": 0.0, "progression": default_progression()}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"best_time": 0.0, "progression": default_progression()}

    if not isinstance(data, dict):
        return {"best_time": 0.0, "progression": default_progression()}

    best_time = data.get("best_time", 0.0)
    if not isinstance(best_time, (int, float)):
        best_time = 0.0

    progression = merge_progression(data.get("progression"))
    progression["totals"]["best_time"] = max(progression["totals"]["best_time"], float(best_time))
    return {"best_time": float(best_time), "progression": progression}


def merge_progression(raw_progression: object) -> dict:
    """Merge save data with the current progression schema."""
    progression = default_progression()
    if not isinstance(raw_progression, dict):
        return progression

    raw_achievements = raw_progression.get("achievements")
    if isinstance(raw_achievements, dict):
        for key in progression["achievements"]:
            value = raw_achievements.get(key)
            if isinstance(value, dict):
                progression["achievements"][key].update(value)

    raw_totals = raw_progression.get("totals")
    if isinstance(raw_totals, dict):
        for key, default_value in DEFAULT_PROGRESS_TOTALS.items():
            value = raw_totals.get(key)
            if isinstance(default_value, float) and isinstance(value, (int, float)):
                progression["totals"][key] = float(value)
            elif isinstance(default_value, int) and isinstance(value, int):
                progression["totals"][key] = value

    selected_skin = raw_progression.get("selected_skin")
    if isinstance(selected_skin, str):
        progression["selected_skin"] = selected_skin

    return progression


def write_save_data(best_time: float, progression: dict) -> None:
    """Persist best-time and progression data without failing the game on write errors."""
    path = save_path()
    payload = {
        "best_time": round(float(best_time), 2),
        "progression": progression,
    }
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        return


def load_best_time() -> float:
    """Load the saved best survival time, falling back to zero on bad data."""
    return float(load_save_data()["best_time"])


def save_best_time(best_time: float) -> None:
    """Persist best survival time while preserving progression data."""
    data = load_save_data()
    progression = data["progression"]
    progression["totals"]["best_time"] = max(progression["totals"]["best_time"], float(best_time))
    write_save_data(best_time, progression)


def load_progression() -> dict:
    """Load the current progression state, merging older save files when needed."""
    return load_save_data()["progression"]


def save_progression(best_time: float, progression: dict) -> None:
    """Persist progression data together with the current best survival time."""
    progression["totals"]["best_time"] = max(progression["totals"]["best_time"], float(best_time))
    write_save_data(best_time, progression)
