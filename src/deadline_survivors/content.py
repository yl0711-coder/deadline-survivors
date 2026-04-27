from __future__ import annotations

from .constants import (
    ACCENT,
    ALERT_COLOR,
    BLUE,
    BUG_COLOR,
    GREEN,
    MEETING_COLOR,
    MUTED,
    OUTAGE_COLOR,
    PLAYER_COLOR,
    PROJECTILE_COLOR,
    PURPLE,
    SCOPE_COLOR,
    XP_COLOR,
)
from .models import Difficulty, EnemyType, Phase, Upgrade


ENEMY_TYPES = [
    EnemyType("Bug", 16, 98, 18, 6, BUG_COLOR, 1.0),
    EnemyType("Meeting", 24, 68, 48, 10, MEETING_COLOR, 0.45),
    EnemyType("Alert", 12, 148, 12, 8, ALERT_COLOR, 0.55),
    EnemyType("Scope Creep", 20, 86, 34, 10, SCOPE_COLOR, 0.35),
]

OUTAGE_BOSS = EnemyType("Outage", 34, 78, 280, 18, OUTAGE_COLOR, 0.0)

UPGRADES = [
    Upgrade("damage", "Patch Notes", "Projectiles deal +6 damage."),
    Upgrade("speed", "Coffee Rush", "Move 12% faster."),
    Upgrade("projectiles", "Multicast", "Ship one extra patch."),
    Upgrade("magnet", "Insight Radar", "Insight shards are pulled from farther away."),
    Upgrade("shield", "Cache Shield", "Gain +18 max health and recover 10 health."),
    Upgrade("pierce", "Rollback Thread", "Patches pierce one extra issue."),
    Upgrade("pulse", "Pager Burst", "Unlock a periodic incident sweep around the player."),
    Upgrade("recovery", "Quiet Hour", "Recover 2 HP every 6 seconds."),
    Upgrade("chain", "Code Review", "Patches chain into nearby issues after a hit."),
    Upgrade("drone", "Pair Programmer", "Add an orbiting helper that ships extra patches."),
    Upgrade("failsafe", "Rollback Guard", "Low health triggers an emergency guard pulse."),
    Upgrade("overclock", "Overclocked Build", "Overdrive patches burst into a small blast."),
]

PHASES = [
    Phase("Warmup", 30.0, 1.28, 0.0),
    Phase("Incident Queue", 42.0, 1.02, 0.22),
    Phase("Alert Storm", 42.0, 0.84, 0.45),
    Phase("Deadline Crunch", 9999.0, 0.66, 0.72),
]

DIFFICULTIES = [
    Difficulty("casual", "Easy", "Softer pressure, more breathing room.", 0.84, 0.82, 1.2, 1.12),
    Difficulty("normal", "Medium", "Default pacing for most runs.", 1.0, 1.0, 1.0, 1.0),
    Difficulty(
        "crunch",
        "Hard",
        "Faster waves and harsher production pain.",
        1.18,
        1.16,
        0.84,
        0.92,
    ),
]

ACHIEVEMENT_DEFS = {
    "first_overdrive": "First Patch Rush",
    "first_deploy": "First Deploy",
    "first_outage": "First Outage",
    "crunch_survivor": "Hard Survivor",
    "deploy_addict": "Deploy Addict",
    "pair_flow": "Pair Flow",
    "review_cascade": "Review Cascade",
    "bug_tracker": "Bug Tracker",
}

ACHIEVEMENT_GROUPS = [
    (
        "Milestones",
        BLUE,
        "First-time moments that teach the run systems.",
        [
            ("first_overdrive", "Reach Overdrive for the first time."),
            ("first_deploy", "Complete a deploy window for the first time."),
            ("first_outage", "Defeat a Production Outage."),
        ],
    ),
    (
        "Challenges",
        ACCENT,
        "Single-run goals that push riskier play.",
        [
            ("crunch_survivor", "Survive 10 minutes on Hard difficulty."),
            ("deploy_addict", "Complete 5 deploys in one run."),
        ],
    ),
    (
        "Build Goals",
        PURPLE,
        "Targets that encourage different upgrade routes.",
        [
            ("pair_flow", "Reach 2 Pair Programmer helpers."),
            ("review_cascade", "Chain through 3 targets in one cascade."),
        ],
    ),
    (
        "Mastery",
        GREEN,
        "Long-term progress across many runs.",
        [
            ("bug_tracker", "Fix 500 bugs across runs."),
        ],
    ),
]

PLAYER_SKINS = {
    "default": {
        "label": "Default",
        "unlock": None,
        "body": BLUE,
        "outline": (52, 116, 205),
        "skin": PLAYER_COLOR,
        "hair": (87, 58, 35),
        "arms": PLAYER_COLOR,
        "screen": GREEN,
    },
    "nightshift": {
        "label": "Night Shift",
        "unlock": "first_deploy",
        "body": (78, 116, 186),
        "outline": (124, 165, 244),
        "skin": (244, 206, 132),
        "hair": (44, 55, 82),
        "arms": (244, 206, 132),
        "screen": (111, 214, 255),
    },
    "incident": {
        "label": "Incident Lead",
        "unlock": "first_outage",
        "body": (214, 98, 98),
        "outline": (255, 152, 152),
        "skin": (252, 214, 154),
        "hair": (99, 37, 37),
        "arms": (252, 214, 154),
        "screen": ACCENT,
    },
    "review": {
        "label": "Code Review",
        "unlock": "review_cascade",
        "body": (139, 104, 210),
        "outline": (207, 177, 255),
        "skin": (240, 209, 154),
        "hair": (70, 48, 102),
        "arms": (240, 209, 154),
        "screen": PURPLE,
    },
    "crunch": {
        "label": "Hard Mode",
        "unlock": "crunch_survivor",
        "body": (104, 151, 113),
        "outline": (161, 226, 173),
        "skin": (244, 209, 153),
        "hair": (46, 71, 38),
        "arms": (244, 209, 153),
        "screen": GREEN,
    },
}

PLAYER_BADGES = {
    "none": {"label": "No Badge", "unlock": None, "color": MUTED},
    "flow": {"label": "Flow Starter", "unlock": "first_overdrive", "color": BLUE},
    "deployer": {"label": "Deploy Runner", "unlock": "first_deploy", "color": GREEN},
    "hunter": {"label": "Outage Hunter", "unlock": "first_outage", "color": OUTAGE_COLOR},
    "reviewer": {"label": "Review Machine", "unlock": "review_cascade", "color": PURPLE},
    "survivor": {"label": "Hard Survivor", "unlock": "crunch_survivor", "color": ACCENT},
}

PATCH_THEMES = {
    "default": {"label": "Default", "unlock": None, "color": PROJECTILE_COLOR},
    "flow": {"label": "Flow Signal", "unlock": "first_overdrive", "color": BLUE},
    "deploy": {"label": "Deploy Green", "unlock": "first_deploy", "color": GREEN},
    "incident": {"label": "Incident Red", "unlock": "first_outage", "color": OUTAGE_COLOR},
    "review": {"label": "Review Purple", "unlock": "review_cascade", "color": PURPLE},
    "tracker": {"label": "Tracker Gold", "unlock": "bug_tracker", "color": XP_COLOR},
}
