from __future__ import annotations

from array import array
from dataclasses import dataclass
from math import atan2, cos, dist, hypot, pi, sin
from random import choice, random
import sys

import pygame

from .constants import (
    ACCENT,
    ALERT_COLOR,
    BG,
    BLUE,
    BUG_COLOR,
    FPS,
    GREEN,
    GRID,
    HEIGHT,
    MEETING_COLOR,
    MUTED,
    OUTAGE_COLOR,
    PANEL,
    PLAYER_COLOR,
    PROJECTILE_COLOR,
    PURPLE,
    RED,
    SCOPE_COLOR,
    TEXT,
    TITLE,
    WIDTH,
    XP_COLOR,
)
from .storage import load_best_time, load_progression, save_best_time, save_progression


@dataclass
class EnemyType:
    name: str
    radius: float
    speed: float
    hp: float
    damage: float
    color: tuple[int, int, int]
    weight: float


@dataclass
class Upgrade:
    key: str
    name: str
    description: str


@dataclass
class Phase:
    name: str
    duration: float
    spawn_base: float
    pressure: float


@dataclass(frozen=True)
class Difficulty:
    key: str
    label: str
    description: str
    enemy_hp_mult: float
    enemy_damage_mult: float
    spawn_interval_mult: float
    insight_mult: float


# Core enemies stay deliberately simple. Difficulty comes from combinations,
# phases, crisis events, and map pressure rather than many complex AI classes.
ENEMY_TYPES = [
    EnemyType("Bug", 16, 98, 18, 6, BUG_COLOR, 1.0),
    EnemyType("Meeting", 24, 68, 48, 10, MEETING_COLOR, 0.45),
    EnemyType("Alert", 12, 148, 12, 8, ALERT_COLOR, 0.55),
    EnemyType("Scope Creep", 20, 86, 34, 10, SCOPE_COLOR, 0.35),
]

OUTAGE_BOSS = EnemyType("Outage", 34, 78, 280, 18, OUTAGE_COLOR, 0.0)

# Level-up upgrades are run-long build choices. Temporary rescue effects such
# as healing, screen clear, and attack haste are handled by powerups instead.
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

# Spawn phases keep the first minute approachable, then gradually add pressure.
PHASES = [
    Phase("Warmup", 30.0, 1.28, 0.0),
    Phase("Incident Queue", 42.0, 1.02, 0.22),
    Phase("Alert Storm", 42.0, 0.84, 0.45),
    Phase("Deadline Crunch", 9999.0, 0.66, 0.72),
]

DIFFICULTIES = [
    Difficulty("casual", "Casual", "Softer pressure, more breathing room.", 0.84, 0.82, 1.2, 1.12),
    Difficulty("normal", "Normal", "Default pacing for most runs.", 1.0, 1.0, 1.0, 1.0),
    Difficulty(
        "crunch",
        "Crunch",
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
    "crunch_survivor": "Crunch Survivor",
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
            ("crunch_survivor", "Survive 10 minutes on Crunch difficulty."),
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
        "label": "Crunch Mode",
        "unlock": "crunch_survivor",
        "body": (104, 151, 113),
        "outline": (161, 226, 173),
        "skin": (244, 209, 153),
        "hair": (46, 71, 38),
        "arms": (244, 209, 153),
        "screen": GREEN,
    },
}


class Game:
    def __init__(self) -> None:
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.large_font = pygame.font.SysFont("consolas", 52, bold=True)
        self.best_time = load_best_time()
        self.progression = load_progression()
        self.selected_difficulty = "normal"
        self.selected_skin = self.progression.get("selected_skin", "default")
        self.sound_enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.fire_sound_timer = 0.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.init_audio()
        self.menu_return_state = "title"
        self.reset()

    def reset(self) -> None:
        """Reset all run-local state before returning to title or starting."""
        self.state = "title"
        self.menu_return_state = "title"
        self.time_survived = 0.0
        self.level = 1
        self.xp = 0.0
        self.xp_to_level = self.xp_required_for_level(self.level)
        self.player_x = WIDTH / 2
        self.player_y = HEIGHT / 2
        self.player_dx = 0.0
        self.player_dy = 0.0
        self.player_radius = 18
        self.player_speed = 265.0
        self.player_hp = 100.0
        self.player_max_hp = 100.0
        self.projectile_damage = 22.0
        self.projectile_speed = 470.0
        self.projectile_count = 1
        self.attack_cooldown = 0.48
        self.attack_timer = 0.08
        self.pickup_radius = 74.0
        self.contact_timer = 0.0
        self.grace_timer = 0.0
        self.spawn_timer = 1.2
        self.pierce = 0
        self.regen_interval = 0.0
        self.regen_timer = 0.0
        self.pulse_unlocked = False
        self.pulse_cooldown = 4.2
        self.pulse_timer = 1.8
        self.pulse_radius = 130.0
        self.pulse_damage = 22.0
        self.crisis_timer = 24.0
        self.boss_timer = 52.0
        self.crisis_name = ""
        self.crisis_banner_timer = 0.0
        self.hazard_timer = 12.0
        self.objective_timer = 14.0
        self.objective: dict | None = None
        self.objective_successes = 0
        self.focus_timer = 0.0
        self.haste_timer = 0.0
        self.momentum = 0.0
        self.momentum_tier = "Idle"
        self.max_momentum = 0.0
        self.max_chain_hits = 1
        self.chain_count = 0
        self.chain_range = 0.0
        self.drone_count = 0
        self.drone_timer = 0.75
        self.drone_cooldown = 1.1
        self.failsafe_level = 0
        self.failsafe_cooldown = 0.0
        self.overclock_level = 0
        self.fire_sound_timer = 0.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.stats = {
            "insight": 0.0,
            "bugs_fixed": 0,
            "meetings_dodged": 0,
            "alerts_silenced": 0,
            "scope_trimmed": 0,
            "outages_resolved": 0,
            "deploys": 0,
            "powerups": 0,
            "failsafe_triggers": 0,
        }
        self.hit_flash = 0.0
        self.level_flash = 0.0
        self.kill_flash = 0.0
        self.new_achievements: list[str] = []
        self.floating_texts: list[dict] = []
        self.enemies: list[dict] = []
        self.projectiles: list[dict] = []
        self.xp_shards: list[dict] = []
        self.hazards: list[dict] = []
        self.powerups: list[dict] = []
        self.level_choices: list[Upgrade] = []

    def start_run(self) -> None:
        self.reset()
        self.state = "playing"

    def current_difficulty(self) -> Difficulty:
        return next(
            difficulty for difficulty in DIFFICULTIES if difficulty.key == self.selected_difficulty
        )

    def unlocked_skins(self) -> list[str]:
        skins = []
        for key, skin in PLAYER_SKINS.items():
            unlock_key = skin["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                skins.append(key)
        return skins

    def current_skin(self) -> dict:
        if self.selected_skin not in self.unlocked_skins():
            self.selected_skin = "default"
            self.progression["selected_skin"] = self.selected_skin
        return PLAYER_SKINS[self.selected_skin]

    def cycle_skin(self) -> None:
        skins = self.unlocked_skins()
        current_index = skins.index(self.selected_skin) if self.selected_skin in skins else 0
        self.selected_skin = skins[(current_index + 1) % len(skins)]
        self.progression["selected_skin"] = self.selected_skin
        save_progression(self.best_time, self.progression)

    def init_audio(self) -> None:
        """Create small procedural sounds so the game has feedback without assets."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.sound_enabled = False
            self.sounds = {}
            return

        self.sound_enabled = True
        self.sounds = {
            "patch": self.build_tone(760, 45, 0.18, 0.35),
            "level": self.build_chord((520, 660, 820), 160, 0.22),
            "pickup": self.build_tone(940, 70, 0.2, 0.22),
            "hit": self.build_tone(180, 90, 0.24, 0.18),
            "deploy": self.build_chord((420, 560, 740), 140, 0.18),
            "crisis": self.build_tone(130, 220, 0.22, 0.05),
            "fail": self.build_chord((280, 210, 160), 260, 0.22),
            "pause": self.build_tone(540, 90, 0.18, 0.18),
        }

    def build_tone(
        self,
        frequency: float,
        duration_ms: int,
        volume: float,
        decay: float,
    ) -> pygame.mixer.Sound:
        sample_rate = 44100
        sample_count = int(sample_rate * (duration_ms / 1000))
        samples = array("h")
        for index in range(sample_count):
            t = index / sample_rate
            envelope = max(0.0, 1.0 - (index / max(1, sample_count)) / max(decay, 0.01))
            value = int(32767 * volume * envelope * sin(2 * pi * frequency * t))
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def build_chord(
        self,
        frequencies: tuple[float, ...],
        duration_ms: int,
        volume: float,
    ) -> pygame.mixer.Sound:
        sample_rate = 44100
        sample_count = int(sample_rate * (duration_ms / 1000))
        samples = array("h")
        for index in range(sample_count):
            t = index / sample_rate
            envelope = max(0.0, 1.0 - index / max(1, sample_count))
            mixed = sum(sin(2 * pi * frequency * t) for frequency in frequencies) / len(frequencies)
            value = int(32767 * volume * envelope * mixed)
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play_sound(self, key: str) -> None:
        if self.sound_enabled and key in self.sounds:
            self.sounds[key].play()

    def trigger_screen_shake(self, duration: float, strength: float) -> None:
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_strength = max(self.shake_strength, strength)

    def choose_upgrade(self, key: str) -> None:
        """Apply a run-long level-up upgrade."""
        if key == "damage":
            self.projectile_damage += 8
            self.spawn_floating_text(self.player_x, self.player_y - 44, "+8 damage", ACCENT)
        elif key == "speed":
            self.player_speed *= 1.15
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Move up", BLUE)
        elif key == "projectiles":
            if self.projectile_count < 5:
                self.projectile_count += 1
                self.spawn_floating_text(self.player_x, self.player_y - 44, "+1 patch", PURPLE)
            else:
                self.attack_cooldown *= 0.94
                self.projectile_damage += 2
                self.spawn_floating_text(
                    self.player_x,
                    self.player_y - 44,
                    "Multicast tuned",
                    PURPLE,
                )
        elif key == "magnet":
            self.pickup_radius += 26
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Radar up", XP_COLOR)
        elif key == "shield":
            self.player_max_hp += 24
            self.player_hp = min(self.player_max_hp, self.player_hp + 14)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Shield up", BLUE)
        elif key == "pierce":
            self.pierce += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Pierce +1", PURPLE)
        elif key == "pulse":
            self.pulse_unlocked = True
            self.pulse_timer = min(self.pulse_timer, 1.0)
            self.pulse_radius += 22
            self.pulse_damage += 8
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Pulse online", PURPLE)
        elif key == "recovery":
            self.regen_interval = (
                6.0 if self.regen_interval == 0 else max(2.7, self.regen_interval * 0.82)
            )
            self.regen_timer = self.regen_interval
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Recovery up", BLUE)
        elif key == "chain":
            self.chain_count += 1
            self.chain_range = 120 + self.chain_count * 20
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Code review", PURPLE)
        elif key == "drone":
            self.drone_count += 1
            self.drone_cooldown = max(0.34, self.drone_cooldown * 0.86)
            self.drone_timer = min(self.drone_timer, 0.35)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Pair online", GREEN)
        elif key == "failsafe":
            self.failsafe_level += 1
            self.failsafe_cooldown = min(self.failsafe_cooldown, 3.0)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Guard armed", BLUE)
        elif key == "overclock":
            self.overclock_level += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Build overclocked", ACCENT)
        self.play_sound("level")

    def run(self) -> int:
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 0
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 0
                    if self.state == "achievements":
                        if event.key in (pygame.K_a, pygame.K_BACKSPACE):
                            self.state = self.menu_return_state
                        continue
                    if self.state in {"playing", "paused"} and event.key == pygame.K_p:
                        self.state = "paused" if self.state == "playing" else "playing"
                        self.play_sound("pause")
                        continue
                    if self.state in {"title", "game_over"}:
                        if event.key == pygame.K_a:
                            self.menu_return_state = self.state
                            self.state = "achievements"
                            continue
                        if event.key == pygame.K_s:
                            self.cycle_skin()
                            continue
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.selected_difficulty = "casual"
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.selected_difficulty = "normal"
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            self.selected_difficulty = "crunch"
                    if self.state in {"title", "game_over"} and event.key == pygame.K_SPACE:
                        self.start_run()
                    elif self.state == "level_up":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.pick_choice(0)
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.pick_choice(1)
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            self.pick_choice(2)

            if self.state == "playing":
                self.update(dt)

            self.draw()
            pygame.display.flip()

    def pick_choice(self, index: int) -> None:
        if 0 <= index < len(self.level_choices):
            self.choose_upgrade(self.level_choices[index].key)
            self.level_choices = []
            self.state = "playing"

    def update(self, dt: float) -> None:
        """Advance one gameplay frame while the run is active."""
        self.time_survived += dt
        self.contact_timer = max(0.0, self.contact_timer - dt)
        self.grace_timer = max(0.0, self.grace_timer - dt)
        self.attack_timer -= dt
        self.spawn_timer -= dt
        self.hit_flash = max(0.0, self.hit_flash - dt * 2.6)
        self.level_flash = max(0.0, self.level_flash - dt * 1.8)
        self.kill_flash = max(0.0, self.kill_flash - dt * 4.2)
        self.crisis_banner_timer = max(0.0, self.crisis_banner_timer - dt)
        self.focus_timer = max(0.0, self.focus_timer - dt)
        self.haste_timer = max(0.0, self.haste_timer - dt)
        self.fire_sound_timer = max(0.0, self.fire_sound_timer - dt)
        self.shake_timer = max(0.0, self.shake_timer - dt)
        self.failsafe_cooldown = max(0.0, self.failsafe_cooldown - dt)
        if self.shake_timer <= 0:
            self.shake_strength = 0.0

        self.move_player(dt)
        self.update_momentum(dt)
        self.update_regen(dt)
        self.update_drone(dt)
        self.update_objective(dt)
        self.update_crisis_director(dt)
        self.update_boss_director(dt)
        self.update_hazards(dt)

        if self.spawn_timer <= 0:
            self.spawn_enemy()
            phase = self.current_phase()
            spawn_base = phase.spawn_base * self.current_difficulty().spawn_interval_mult
            self.spawn_timer = max(0.18, spawn_base - min(self.time_survived / 72, 0.18))

        if self.attack_timer <= 0:
            self.fire_projectiles()
            self.attack_timer = self.effective_attack_cooldown()
        if self.pulse_unlocked:
            self.update_pulse(dt)

        self.update_projectiles(dt)
        self.update_enemies(dt)
        self.update_xp(dt)
        self.update_powerups(dt)
        self.update_floating_texts(dt)
        self.check_level_up()

        if self.player_hp <= 0:
            self.state = "game_over"
            self.play_sound("fail")
            if self.time_survived > self.best_time:
                self.best_time = self.time_survived
                save_best_time(self.best_time)
            self.finalize_run_progression()

    def current_phase(self) -> Phase:
        elapsed = self.time_survived
        phase_start = 0.0
        for phase in PHASES:
            if elapsed < phase_start + phase.duration:
                return phase
            phase_start += phase.duration
        return PHASES[-1]

    def update_regen(self, dt: float) -> None:
        if self.regen_interval <= 0 or self.player_hp >= self.player_max_hp:
            return
        self.regen_timer -= dt
        if self.regen_timer <= 0:
            self.player_hp = min(self.player_max_hp, self.player_hp + 2)
            self.regen_timer = self.regen_interval
            self.spawn_floating_text(self.player_x, self.player_y - 20, "+2", BLUE)

    def update_momentum(self, dt: float) -> None:
        """Reward active movement with visible Flow and Overdrive tiers."""
        previous_tier = self.momentum_tier
        moving = self.player_dx != 0 or self.player_dy != 0
        if moving:
            self.momentum = min(1.0, self.momentum + dt * 0.9)
        else:
            self.momentum = max(0.0, self.momentum - dt * 1.15)
        self.max_momentum = max(self.max_momentum, self.momentum)

        self.momentum_tier = self.current_momentum_tier()
        if self.momentum_tier != previous_tier and self.momentum_tier != "Idle":
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 66,
                self.momentum_tier,
                GREEN,
            )
            if self.momentum_tier == "Overdrive":
                self.unlock_achievement("first_overdrive")

    def current_momentum_tier(self) -> str:
        if self.momentum >= 0.8:
            return "Overdrive"
        if self.momentum >= 0.35:
            return "Flow"
        return "Idle"

    def update_objective(self, dt: float) -> None:
        """Update optional deploy windows and their risk-reward progress."""
        if self.objective is None:
            if self.time_survived < 18 and self.level < 4:
                return
            self.objective_timer -= dt
            if self.objective_timer <= 0:
                self.spawn_objective()
            return

        objective = self.objective
        objective["ttl"] -= dt
        inside = (
            dist((self.player_x, self.player_y), (objective["x"], objective["y"]))
            <= objective["radius"]
        )
        if inside:
            objective["progress"] += dt * (1.0 + self.momentum * 0.25)
        else:
            objective["progress"] = max(0.0, objective["progress"] - dt * 0.35)

        if objective["progress"] >= objective["required"]:
            self.complete_objective(objective)
        elif objective["ttl"] <= 0:
            self.objective = None
            self.objective_timer = max(9.0, 18.0 - min(self.level, 16) * 0.45)

    def spawn_objective(self) -> None:
        angle = random() * pi * 2
        distance_from_player = 190 + random() * 260
        radius = 54.0
        x = max(radius, min(WIDTH - radius, self.player_x + cos(angle) * distance_from_player))
        y = max(radius, min(HEIGHT - radius, self.player_y + sin(angle) * distance_from_player))
        self.objective = {
            "name": "Deploy Window",
            "x": x,
            "y": y,
            "radius": radius,
            "progress": 0.0,
            "required": 2.15,
            "ttl": 16.0,
            "reward": 16.0 + self.level * 2.0,
        }
        self.spawn_floating_text(x - 42, y - 76, "Deploy window", GREEN)

    def complete_objective(self, objective: dict) -> None:
        reward = objective["reward"]
        self.xp += reward
        self.stats["insight"] += reward
        self.focus_timer = 6.0
        self.objective_successes += 1
        self.stats["deploys"] += 1
        self.player_hp = min(self.player_max_hp, self.player_hp + 6)
        self.spawn_floating_text(
            objective["x"] - 36,
            objective["y"] - 72,
            f"+{int(reward)} insight",
            XP_COLOR,
        )
        self.spawn_floating_text(self.player_x, self.player_y - 48, "Focus mode", GREEN)
        self.play_sound("deploy")
        self.unlock_achievement("first_deploy")
        self.objective = None
        self.objective_timer = max(8.0, 20.0 - min(self.level, 18) * 0.5)

    def update_pulse(self, dt: float) -> None:
        self.pulse_timer -= dt
        if self.pulse_timer > 0:
            return
        self.pulse_timer = self.pulse_cooldown
        hit_count = 0
        for enemy in self.enemies:
            if dist((self.player_x, self.player_y), (enemy["x"], enemy["y"])) <= self.pulse_radius:
                enemy["hp"] -= self.pulse_damage
                hit_count += 1
        if hit_count:
            self.kill_flash = 0.22
            self.trigger_screen_shake(0.12, 2.0)
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 42,
                f"Pulse x{hit_count}",
                PURPLE,
            )

    def update_drone(self, dt: float) -> None:
        if self.drone_count <= 0 or not self.enemies:
            return
        self.drone_timer -= dt
        if self.drone_timer > 0:
            return

        self.drone_timer = self.drone_cooldown
        damage_multiplier = 0.58 + min(0.3, self.drone_count * 0.08)
        orbit_radius = 34
        for index in range(self.drone_count):
            angle = self.time_survived * 2.4 + index * (2 * pi / max(1, self.drone_count))
            origin_x = self.player_x + cos(angle) * orbit_radius
            origin_y = self.player_y + sin(angle) * orbit_radius
            target = min(
                self.enemies,
                key=lambda enemy: dist((origin_x, origin_y), (enemy["x"], enemy["y"])),
            )
            shot_angle = atan2(target["y"] - origin_y, target["x"] - origin_x)
            self.projectiles.append(
                {
                    "x": origin_x,
                    "y": origin_y,
                    "vx": cos(shot_angle) * self.projectile_speed * 0.88,
                    "vy": sin(shot_angle) * self.projectile_speed * 0.88,
                    "damage": self.projectile_damage * damage_multiplier,
                    "radius": max(4, self.projectile_radius() - 1),
                    "color": BLUE,
                    "pierce": max(0, self.pierce - 1),
                    "source": "drone",
                    "chain": max(0, self.chain_count - 1),
                    "chain_range": self.chain_range,
                }
            )
        if self.fire_sound_timer <= 0:
            self.play_sound("patch")
            self.fire_sound_timer = 0.08

    def move_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        dy = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        length = hypot(dx, dy)
        if length:
            dx /= length
            dy /= length
        self.player_dx = dx
        self.player_dy = dy

        self.player_x = max(
            self.player_radius,
            min(WIDTH - self.player_radius, self.player_x + dx * self.player_speed * dt),
        )
        self.player_y = max(
            self.player_radius,
            min(HEIGHT - self.player_radius, self.player_y + dy * self.player_speed * dt),
        )

    def spawn_enemy(self) -> None:
        enemy_type = self.pick_enemy_type()
        self.add_enemy(enemy_type)

    def add_enemy(
        self,
        enemy_type: EnemyType,
        elite: bool | None = None,
        near_player: bool = False,
    ) -> None:
        if elite is None:
            elite_chance = 0.0
            if self.level >= 8:
                elite_chance += 0.03
            if self.level >= 12:
                elite_chance += 0.05
            if self.current_phase().name == "Deadline Crunch":
                elite_chance += 0.04
            elite = random() < elite_chance

        if near_player:
            angle = random() * pi * 2
            distance_from_player = 280 + random() * 140
            x = max(
                30,
                min(WIDTH - 30, self.player_x + cos(angle) * distance_from_player),
            )
            y = max(
                30,
                min(HEIGHT - 30, self.player_y + sin(angle) * distance_from_player),
            )
        else:
            side = choice(["top", "bottom", "left", "right"])
            if side == "top":
                x, y = random() * WIDTH, -30
            elif side == "bottom":
                x, y = random() * WIDTH, HEIGHT + 30
            elif side == "left":
                x, y = -30, random() * HEIGHT
            else:
                x, y = WIDTH + 30, random() * HEIGHT

        level_pressure = max(0, self.level - 7) * 2.15
        elite_multiplier = 2.2 if elite else 1.0
        difficulty = self.current_difficulty()
        self.enemies.append(
            {
                "type": enemy_type,
                "x": x,
                "y": y,
                "hp": (
                    enemy_type.hp
                    + level_pressure
                    + self.time_survived * (0.35 + self.current_phase().pressure * 0.22)
                )
                * difficulty.enemy_hp_mult
                * elite_multiplier,
                "damage": enemy_type.damage * difficulty.enemy_damage_mult,
                "dash_timer": 0.0,
                "dash_cooldown": 1.4 + random() * 0.9,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 1 if enemy_type.name == "Scope Creep" else 0,
                "elite": elite,
            }
        )

    def update_crisis_director(self, dt: float) -> None:
        """Occasionally inject a themed burst of enemies after the safe opening."""
        if self.time_survived < 55:
            return

        self.crisis_timer -= dt
        if self.crisis_timer > 0:
            return

        self.crisis_timer = max(14.0, 28.0 - min(self.level, 20) * 0.45)
        crisis = choice(["Standup Swarm", "Pager Storm", "Scope Review"])
        self.crisis_name = crisis
        self.crisis_banner_timer = 2.4
        self.spawn_floating_text(self.player_x, self.player_y - 70, crisis, RED)
        self.play_sound("crisis")
        self.trigger_screen_shake(0.2, 3.0)

        if crisis == "Standup Swarm":
            bug = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug")
            meeting = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Meeting")
            for _ in range(5):
                self.add_enemy(bug, elite=False, near_player=True)
            self.add_enemy(meeting, elite=self.level >= 10, near_player=True)
        elif crisis == "Pager Storm":
            alert = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Alert")
            for index in range(4):
                self.add_enemy(alert, elite=index == 0 and self.level >= 12, near_player=True)
        else:
            scope = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Scope Creep")
            meeting = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Meeting")
            for _ in range(2):
                self.add_enemy(scope, elite=self.level >= 14 and random() < 0.5, near_player=True)
            self.add_enemy(meeting, elite=False, near_player=True)

    def update_boss_director(self, dt: float) -> None:
        if self.time_survived < 72 and self.level < 8:
            return
        if any(enemy["type"].name == "Outage" for enemy in self.enemies):
            return

        self.boss_timer -= dt
        if self.boss_timer > 0:
            return

        self.boss_timer = max(34.0, 58.0 - min(self.level, 18) * 1.15)
        self.spawn_outage_boss()

    def spawn_outage_boss(self) -> None:
        angle = random() * pi * 2
        distance_from_player = 320 + random() * 90
        x = max(42, min(WIDTH - 42, self.player_x + cos(angle) * distance_from_player))
        y = max(42, min(HEIGHT - 42, self.player_y + sin(angle) * distance_from_player))
        difficulty = self.current_difficulty()
        hp = (
            OUTAGE_BOSS.hp
            + max(0, self.level - 8) * 18
            + self.time_survived * 0.95
        ) * difficulty.enemy_hp_mult
        self.enemies.append(
            {
                "type": OUTAGE_BOSS,
                "x": x,
                "y": y,
                "hp": hp,
                "max_hp": hp,
                "damage": OUTAGE_BOSS.damage * difficulty.enemy_damage_mult,
                "dash_timer": 0.0,
                "dash_cooldown": 99.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": True,
                "boss": True,
                "pulse_timer": 2.4,
                "summon_timer": 4.8,
                "rage": False,
            }
        )
        self.crisis_name = "Production Outage"
        self.crisis_banner_timer = 2.8
        self.play_sound("crisis")
        self.trigger_screen_shake(0.22, 4.8)
        self.spawn_floating_text(x - 46, y - 76, "Production Outage", RED)

    def update_hazards(self, dt: float) -> None:
        """Create red floor pressure so strong builds still need to move."""
        if self.time_survived >= 60 or self.level >= 10:
            self.hazard_timer -= dt
            if self.hazard_timer <= 0:
                self.spawn_hazard()
                pressure = min(
                    6.0,
                    max(0, self.level - 8) * 0.42 + self.current_phase().pressure * 2.4,
                )
                self.hazard_timer = max(4.4, 10.5 - pressure)

        active_hazards = []
        for hazard in self.hazards:
            hazard["warn"] -= dt
            if hazard["warn"] <= 0:
                hazard["duration"] -= dt
                if (
                    not hazard["hit"]
                    and self.grace_timer <= 0
                    and dist((self.player_x, self.player_y), (hazard["x"], hazard["y"]))
                    <= hazard["radius"] + self.player_radius
                ):
                    self.player_hp -= hazard["damage"]
                    self.grace_timer = 0.5
                    self.hit_flash = 0.45
                    hazard["hit"] = True
                    self.spawn_floating_text(
                        self.player_x,
                        self.player_y - 30,
                        f"-{int(hazard['damage'])} zone",
                        RED,
                    )
            if hazard["duration"] > 0:
                active_hazards.append(hazard)
        self.hazards = active_hazards

    def spawn_hazard(self) -> None:
        radius = min(98.0, 64.0 + max(0, self.level - 10) * 3.0)
        lead_x = self.player_dx * 68.0
        lead_y = self.player_dy * 68.0
        jitter_x = (random() - 0.5) * 60.0
        jitter_y = (random() - 0.5) * 60.0
        x = max(radius, min(WIDTH - radius, self.player_x + lead_x + jitter_x))
        y = max(radius, min(HEIGHT - radius, self.player_y + lead_y + jitter_y))
        damage = 12.0 + min(12.0, max(0, self.level - 10) * 1.0)
        self.hazards.append(
            {
                "x": x,
                "y": y,
                "radius": radius,
                "warn": 1.05,
                "duration": 1.65,
                "damage": damage,
                "hit": False,
            }
        )

    def pick_enemy_type(self) -> EnemyType:
        available = []
        phase = self.current_phase()
        for enemy_type in ENEMY_TYPES:
            weight = enemy_type.weight
            if phase.name == "Warmup":
                if enemy_type.name == "Meeting":
                    weight *= 0.12
                if enemy_type.name == "Alert":
                    weight *= 0.35
                if enemy_type.name == "Scope Creep":
                    weight *= 0.05
            elif phase.name == "Incident Queue":
                if enemy_type.name == "Meeting":
                    weight *= 0.6
                if enemy_type.name == "Scope Creep":
                    weight *= 0.22
            elif phase.name == "Alert Storm":
                if enemy_type.name == "Alert":
                    weight *= 1.28
                if enemy_type.name == "Meeting":
                    weight *= 0.82
                if enemy_type.name == "Scope Creep":
                    weight *= 0.6
            elif phase.name == "Deadline Crunch":
                if enemy_type.name == "Meeting":
                    weight *= 1.12
                if enemy_type.name == "Scope Creep":
                    weight *= 1.34
            available.extend([enemy_type] * max(1, int(weight * 10)))
        return choice(available)

    def fire_projectiles(self) -> None:
        if not self.enemies:
            return

        sorted_enemies = sorted(
            self.enemies,
            key=lambda enemy: dist((self.player_x, self.player_y), (enemy["x"], enemy["y"])),
        )
        targets = sorted_enemies[: min(self.projectile_count, 6)]
        damage_multiplier = self.projectile_damage_multiplier()
        for target in targets:
            angle = atan2(target["y"] - self.player_y, target["x"] - self.player_x)
            self.projectiles.append(
                {
                    "x": self.player_x,
                    "y": self.player_y,
                    "vx": cos(angle) * self.projectile_speed,
                    "vy": sin(angle) * self.projectile_speed,
                    "damage": self.projectile_damage
                    * damage_multiplier
                    * self.momentum_damage_multiplier(),
                    "radius": self.projectile_radius(),
                    "color": self.projectile_color(),
                    "pierce": self.pierce,
                    "source": "player",
                    "chain": self.chain_count,
                    "chain_range": self.chain_range,
                }
            )
        if self.fire_sound_timer <= 0:
            self.play_sound("patch")
            self.fire_sound_timer = 0.08

    def effective_attack_cooldown(self) -> float:
        focus_bonus = 0.72 if self.focus_timer > 0 else 1.0
        haste_bonus = 0.62 if self.haste_timer > 0 else 1.0
        movement_bonus = 1.0 - self.momentum * 0.22
        return max(0.14, self.attack_cooldown * focus_bonus * haste_bonus * movement_bonus)

    def momentum_damage_multiplier(self) -> float:
        if self.momentum_tier == "Overdrive":
            return 1.12
        if self.momentum_tier == "Flow":
            return 1.05
        return 1.0

    def projectile_radius(self) -> int:
        if self.momentum_tier == "Overdrive":
            return 7
        if self.momentum_tier == "Flow":
            return 6
        return 5

    def projectile_color(self) -> tuple[int, int, int]:
        if self.momentum_tier == "Overdrive":
            return GREEN
        if self.momentum_tier == "Flow":
            return ACCENT
        return PROJECTILE_COLOR

    def update_projectiles(self, dt: float) -> None:
        next_projectiles = []
        spawned_projectiles = []
        for projectile in self.projectiles:
            projectile["x"] += projectile["vx"] * dt
            projectile["y"] += projectile["vy"] * dt
            if not (
                -40 <= projectile["x"] <= WIDTH + 40
                and -40 <= projectile["y"] <= HEIGHT + 40
            ):
                continue

            hit = False
            for enemy in self.enemies:
                if (
                    dist((projectile["x"], projectile["y"]), (enemy["x"], enemy["y"]))
                    <= projectile["radius"] + enemy["type"].radius
                ):
                    enemy["hp"] -= projectile["damage"]
                    self.trigger_screen_shake(0.05, 1.0)
                    self.spawn_floating_text(
                        enemy["x"],
                        enemy["y"] - 12,
                        str(int(projectile["damage"])),
                        ACCENT,
                    )
                    hit = True
                    if projectile["pierce"] > 0:
                        projectile["pierce"] -= 1
                        self.try_chain_projectile(projectile, enemy, spawned_projectiles)
                        hit = False
                    else:
                        self.try_chain_projectile(projectile, enemy, spawned_projectiles)
                        self.trigger_overclock_burst(projectile, enemy)
                        break
            if not hit:
                next_projectiles.append(projectile)
        self.projectiles = next_projectiles + spawned_projectiles

    def try_chain_projectile(
        self,
        projectile: dict,
        source_enemy: dict,
        spawned_projectiles: list[dict],
    ) -> None:
        if projectile.get("chain", 0) <= 0:
            return
        target = self.find_chain_target(
            source_enemy,
            projectile.get("chain_range", self.chain_range),
        )
        if target is None:
            return
        remaining_chain = projectile["chain"] - 1
        chain_hits = projectile.get("chain_hits", 1) + 1
        self.max_chain_hits = max(self.max_chain_hits, chain_hits)
        angle = atan2(target["y"] - source_enemy["y"], target["x"] - source_enemy["x"])
        spawned_projectiles.append(
            {
                "x": source_enemy["x"],
                "y": source_enemy["y"],
                "vx": cos(angle) * self.projectile_speed * 1.04,
                "vy": sin(angle) * self.projectile_speed * 1.04,
                "damage": projectile["damage"] * 0.82,
                "radius": max(4, projectile["radius"] - 1),
                "color": PURPLE,
                "pierce": 0,
                "source": "chain",
                "chain": max(0, remaining_chain),
                "chain_hits": chain_hits,
                "chain_range": projectile.get("chain_range", self.chain_range),
            }
        )
        self.spawn_floating_text(source_enemy["x"], source_enemy["y"] - 26, "review", PURPLE)

    def find_chain_target(self, source_enemy: dict, max_range: float) -> dict | None:
        candidates = [
            enemy
            for enemy in self.enemies
            if enemy is not source_enemy
            and dist((source_enemy["x"], source_enemy["y"]), (enemy["x"], enemy["y"])) <= max_range
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda enemy: dist((source_enemy["x"], source_enemy["y"]), (enemy["x"], enemy["y"])),
        )

    def trigger_overclock_burst(self, projectile: dict, source_enemy: dict) -> None:
        if self.overclock_level <= 0 or self.momentum_tier != "Overdrive":
            return
        radius = 42 + self.overclock_level * 14
        damage = projectile["damage"] * (0.28 + self.overclock_level * 0.05)
        hit_count = 0
        for enemy in self.enemies:
            if enemy is source_enemy:
                continue
            if dist((source_enemy["x"], source_enemy["y"]), (enemy["x"], enemy["y"])) <= radius:
                enemy["hp"] -= damage
                hit_count += 1
        if hit_count:
            self.kill_flash = max(self.kill_flash, 0.12)
            self.trigger_screen_shake(0.06, 1.6)
            self.spawn_floating_text(source_enemy["x"] - 14, source_enemy["y"] - 34, "burst", ACCENT)

    def update_enemies(self, dt: float) -> None:
        alive = []
        for enemy in self.enemies:
            self.advance_enemy(enemy, dt)

            if (
                dist((self.player_x, self.player_y), (enemy["x"], enemy["y"]))
                <= self.player_radius + enemy["type"].radius
            ):
                if self.contact_timer <= 0 and self.grace_timer <= 0:
                    self.player_hp -= enemy.get("damage", enemy["type"].damage)
                    self.contact_timer = 0.25
                    self.grace_timer = 0.55
                    self.hit_flash = 0.42
                    self.play_sound("hit")
                    self.trigger_screen_shake(0.14, 4.0)
                    self.spawn_floating_text(
                        self.player_x,
                        self.player_y - 28,
                        f"-{int(enemy.get('damage', enemy['type'].damage))}",
                        RED,
                    )
                    self.trigger_failsafe()

            if enemy["hp"] <= 0:
                value = 3.0
                if enemy["type"].name == "Meeting":
                    value = 6.0
                elif enemy["type"].name == "Scope Creep":
                    value = 7.0
                elif enemy["type"].name == "Alert":
                    value = 4.0
                elif enemy["type"].name == "Outage":
                    value = 24.0
                self.xp_shards.append({"x": enemy["x"], "y": enemy["y"], "value": value})
                self.spawn_fix_text(enemy)
                self.maybe_drop_powerup(enemy)
                self.track_enemy_resolution(enemy)
                if enemy["type"].name == "Scope Creep" and enemy.get("split_depth", 0) > 0:
                    self.spawn_scope_split(enemy)
                self.kill_flash = 0.18
            else:
                alive.append(enemy)

        self.enemies = alive

    def trigger_failsafe(self) -> None:
        if self.failsafe_level <= 0 or self.failsafe_cooldown > 0:
            return
        threshold = self.player_max_hp * max(0.2, 0.38 - self.failsafe_level * 0.03)
        if self.player_hp > threshold:
            return

        self.failsafe_cooldown = max(15.0, 21.0 - self.failsafe_level * 2.0)
        self.grace_timer = max(self.grace_timer, 1.1)
        self.stats["failsafe_triggers"] += 1
        recovered = 12 + self.failsafe_level * 5
        self.player_hp = min(self.player_max_hp, self.player_hp + recovered)
        blast_radius = 120 + self.failsafe_level * 18
        blast_damage = 18 + self.failsafe_level * 8
        hit_count = 0
        for enemy in self.enemies:
            if dist((self.player_x, self.player_y), (enemy["x"], enemy["y"])) <= blast_radius:
                enemy["hp"] -= blast_damage
                hit_count += 1
        self.play_sound("crisis")
        self.trigger_screen_shake(0.16, 4.6)
        self.spawn_floating_text(self.player_x, self.player_y - 54, "Rollback Guard", BLUE)
        if hit_count:
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 28,
                f"stabilized x{hit_count}",
                ACCENT,
            )

    def spawn_fix_text(self, enemy: dict) -> None:
        labels = {
            "Bug": "bug fixed",
            "Meeting": "meeting dodged",
            "Alert": "alert silenced",
            "Scope Creep": "scope trimmed",
            "Bugling": "tiny bug fixed",
            "Outage": "outage resolved",
        }
        self.spawn_floating_text(
            enemy["x"] - enemy["type"].radius,
            enemy["y"] - enemy["type"].radius - 10,
            labels.get(enemy["type"].name, "issue fixed"),
            XP_COLOR,
        )

    def track_enemy_resolution(self, enemy: dict) -> None:
        stat_map = {
            "Bug": "bugs_fixed",
            "Bugling": "bugs_fixed",
            "Meeting": "meetings_dodged",
            "Alert": "alerts_silenced",
            "Scope Creep": "scope_trimmed",
            "Outage": "outages_resolved",
        }
        stat_key = stat_map.get(enemy["type"].name)
        if stat_key is not None:
            self.stats[stat_key] += 1
        if enemy["type"].name == "Outage":
            self.unlock_achievement("first_outage")

    def maybe_drop_powerup(self, enemy: dict) -> None:
        """Drop short-term rescue tools without polluting level-up choices."""
        if enemy["type"].name == "Outage":
            self.spawn_powerup(choice(["heal", "bomb", "haste"]), enemy["x"], enemy["y"])
            return
        drop_roll = random()
        drop_bonus = 0.04 if enemy["type"].name in {"Meeting", "Scope Creep"} else 0.0
        if drop_roll >= 0.12 + drop_bonus:
            return

        if self.player_hp < self.player_max_hp * 0.55:
            kind = "heal"
        elif drop_roll < 0.04:
            kind = "bomb"
        elif drop_roll < 0.08:
            kind = "haste"
        else:
            kind = choice(["heal", "haste", "bomb"])
        self.spawn_powerup(kind, enemy["x"], enemy["y"])

    def spawn_powerup(self, kind: str, x: float, y: float) -> None:
        labels = {
            "heal": "Coffee Break",
            "bomb": "Refactor Bomb",
            "haste": "CI Boost",
        }
        colors = {
            "heal": GREEN,
            "bomb": ACCENT,
            "haste": BLUE,
        }
        self.powerups.append(
            {
                "kind": kind,
                "label": labels[kind],
                "color": colors[kind],
                "x": max(24, min(WIDTH - 24, x)),
                "y": max(24, min(HEIGHT - 24, y)),
                "radius": 16,
                "ttl": 14.0,
            }
        )

    def advance_enemy(self, enemy: dict, dt: float) -> None:
        enemy_type = enemy["type"]
        if enemy_type.name == "Outage":
            self.advance_outage(enemy, dt)
            return
        if enemy_type.name == "Meeting":
            target_x = self.player_x + self.player_dx * self.player_speed * 0.55
            target_y = self.player_y + self.player_dy * self.player_speed * 0.55
            angle = atan2(target_y - enemy["y"], target_x - enemy["x"])
            move_speed = enemy_type.speed * 0.92
            enemy["x"] += cos(angle) * move_speed * dt
            enemy["y"] += sin(angle) * move_speed * dt
            return

        if enemy_type.name == "Alert":
            enemy["dash_cooldown"] -= dt
            if enemy["dash_timer"] > 0:
                enemy["dash_timer"] -= dt
                enemy["x"] += enemy["dash_vx"] * dt
                enemy["y"] += enemy["dash_vy"] * dt
                return

            distance_to_player = dist((self.player_x, self.player_y), (enemy["x"], enemy["y"]))
            if enemy["dash_cooldown"] <= 0 and distance_to_player < 220:
                angle = atan2(self.player_y - enemy["y"], self.player_x - enemy["x"])
                enemy["dash_vx"] = cos(angle) * enemy_type.speed * 2.45
                enemy["dash_vy"] = sin(angle) * enemy_type.speed * 2.45
                enemy["dash_timer"] = 0.28
                enemy["dash_cooldown"] = 1.7 + random() * 0.8
                return

        angle = atan2(self.player_y - enemy["y"], self.player_x - enemy["x"])
        enemy["x"] += cos(angle) * enemy_type.speed * dt
        enemy["y"] += sin(angle) * enemy_type.speed * dt

    def advance_outage(self, enemy: dict, dt: float) -> None:
        hp_ratio = enemy["hp"] / max(1.0, enemy.get("max_hp", enemy["hp"]))
        if hp_ratio <= 0.5 and not enemy["rage"]:
            enemy["rage"] = True
            enemy["pulse_timer"] = min(enemy["pulse_timer"], 1.1)
            enemy["summon_timer"] = min(enemy["summon_timer"], 2.3)
            self.spawn_floating_text(enemy["x"] - 22, enemy["y"] - 48, "Outage escalates", RED)

        distance_to_player = dist((self.player_x, self.player_y), (enemy["x"], enemy["y"]))
        preferred_distance = 170
        angle = atan2(self.player_y - enemy["y"], self.player_x - enemy["x"])
        speed = enemy_type.speed * (1.18 if enemy["rage"] else 1.0)
        move_direction = 1.0 if distance_to_player > preferred_distance else -0.72
        enemy["x"] += cos(angle) * speed * move_direction * dt
        enemy["y"] += sin(angle) * speed * move_direction * dt

        enemy["pulse_timer"] -= dt
        if enemy["pulse_timer"] <= 0:
            self.emit_outage_wave(enemy)
            enemy["pulse_timer"] = 1.65 if enemy["rage"] else 2.55

        enemy["summon_timer"] -= dt
        if enemy["summon_timer"] <= 0:
            self.summon_outage_support(enemy)
            enemy["summon_timer"] = 3.1 if enemy["rage"] else 5.0

    def emit_outage_wave(self, enemy: dict) -> None:
        self.trigger_screen_shake(0.1, 2.6)
        self.spawn_floating_text(enemy["x"] - 18, enemy["y"] - 52, "Incident wave", OUTAGE_COLOR)
        for index in range(6):
            angle = index * (2 * pi / 6)
            radius = 54.0
            x = max(radius, min(WIDTH - radius, enemy["x"] + cos(angle) * 92))
            y = max(radius, min(HEIGHT - radius, enemy["y"] + sin(angle) * 92))
            self.hazards.append(
                {
                    "x": x,
                    "y": y,
                    "radius": radius,
                    "warn": 0.85,
                    "duration": 1.2,
                    "damage": 12.0 if not enemy["rage"] else 16.0,
                    "hit": False,
                }
            )

    def summon_outage_support(self, enemy: dict) -> None:
        alert = next(enemy_type for enemy_type in ENEMY_TYPES if enemy_type.name == "Alert")
        bug = next(enemy_type for enemy_type in ENEMY_TYPES if enemy_type.name == "Bug")
        self.spawn_floating_text(enemy["x"] - 26, enemy["y"] - 28, "Escalation", ACCENT)
        self.add_enemy(alert, elite=False, near_player=True)
        self.add_enemy(choice([alert, bug]), elite=False, near_player=True)

    def projectile_damage_multiplier(self) -> float:
        if self.projectile_count <= 1:
            return 1.0
        return max(0.45, 1.0 - (self.projectile_count - 1) * 0.18)

    def spawn_scope_split(self, enemy: dict) -> None:
        for offset in (-16, 16):
            self.enemies.append(
                {
                    "type": EnemyType("Bugling", 12, 122, 16, 8, (218, 170, 255), 0.0),
                    "x": enemy["x"] + offset,
                    "y": enemy["y"] - offset * 0.25,
                    "hp": (
                        16 + self.time_survived * 0.18
                    ) * self.current_difficulty().enemy_hp_mult,
                    "damage": 8 * self.current_difficulty().enemy_damage_mult,
                    "dash_timer": 0.0,
                    "dash_cooldown": 99.0,
                    "dash_vx": 0.0,
                    "dash_vy": 0.0,
                    "split_depth": 0,
                    "elite": False,
                }
            )

    def update_xp(self, dt: float) -> None:
        remaining = []
        for shard in self.xp_shards:
            distance = dist((self.player_x, self.player_y), (shard["x"], shard["y"]))
            pickup_radius = self.effective_pickup_radius()
            if distance <= pickup_radius and distance > 1:
                angle = atan2(self.player_y - shard["y"], self.player_x - shard["x"])
                speed = 260 + (pickup_radius - min(distance, pickup_radius)) * 5
                shard["x"] += cos(angle) * speed * dt
                shard["y"] += sin(angle) * speed * dt

            if (
                dist((self.player_x, self.player_y), (shard["x"], shard["y"]))
                <= self.player_radius + 8
            ):
                gained = shard["value"] * self.xp_multiplier()
                self.xp += gained
                self.stats["insight"] += gained
                if shard["value"] >= 8:
                    self.spawn_floating_text(
                        shard["x"],
                        shard["y"] - 10,
                        f"+{int(gained)} insight",
                        XP_COLOR,
                    )
            else:
                remaining.append(shard)
        self.xp_shards = remaining

    def xp_multiplier(self) -> float:
        focus_bonus = 0.18 if self.focus_timer > 0 else 0.0
        return 1.0 + self.momentum * 0.45 + focus_bonus

    def effective_pickup_radius(self) -> float:
        focus_bonus = 18.0 if self.focus_timer > 0 else 0.0
        return self.pickup_radius * (1.0 + self.momentum * 0.35) + focus_bonus

    def update_powerups(self, dt: float) -> None:
        remaining = []
        for powerup in self.powerups:
            powerup["ttl"] -= dt
            if powerup["ttl"] <= 0:
                continue
            if (
                dist((self.player_x, self.player_y), (powerup["x"], powerup["y"]))
                <= self.player_radius + powerup["radius"]
            ):
                self.apply_powerup(powerup["kind"])
            else:
                remaining.append(powerup)
        self.powerups = remaining

    def apply_powerup(self, kind: str) -> None:
        """Apply immediate or temporary effects from picked-up powerups."""
        self.stats["powerups"] += 1
        if kind == "heal":
            recovered = min(28.0, self.player_max_hp - self.player_hp)
            self.player_hp = min(self.player_max_hp, self.player_hp + 28)
            self.play_sound("pickup")
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 44,
                f"Coffee +{int(recovered)} HP",
                GREEN,
            )
        elif kind == "bomb":
            cleared = len(self.enemies)
            for enemy in self.enemies:
                self.xp_shards.append({"x": enemy["x"], "y": enemy["y"], "value": 3.0})
            self.enemies = []
            self.kill_flash = 0.6
            self.play_sound("crisis")
            self.trigger_screen_shake(0.2, 5.5)
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 52,
                f"Refactor x{cleared}",
                ACCENT,
            )
        elif kind == "haste":
            self.haste_timer = 7.0
            self.play_sound("pickup")
            self.spawn_floating_text(self.player_x, self.player_y - 44, "CI Boost", BLUE)

    def update_floating_texts(self, dt: float) -> None:
        remaining = []
        for item in self.floating_texts:
            item["ttl"] -= dt
            item["y"] -= item["rise"] * dt
            if item["ttl"] > 0:
                remaining.append(item)
        self.floating_texts = remaining

    def spawn_floating_text(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int],
    ) -> None:
        self.floating_texts.append(
            {
                "x": x,
                "y": y,
                "text": text,
                "color": color,
                "ttl": 0.7,
                "rise": 36.0,
            }
        )

    def check_level_up(self) -> None:
        """Enter the upgrade choice state when enough insight has been collected."""
        if self.xp < self.xp_to_level:
            return

        self.xp -= self.xp_to_level
        self.level += 1
        self.xp_to_level = self.xp_required_for_level(self.level)
        self.state = "level_up"
        self.level_choices = self.pick_level_choices()
        self.level_flash = 0.4
        self.spawn_floating_text(self.player_x, self.player_y - 54, f"Level {self.level}", ACCENT)

    def xp_required_for_level(self, level: int) -> float:
        """Return insight needed to advance from current level to the next level.

        The curve is intentionally steeper than enemy insight growth so individual
        shards become a smaller percentage of the bar at higher levels.
        """
        level_index = max(1, level)
        return float(round(70 + (level_index - 1) * 30 + (level_index - 1) ** 2 * 7))

    def pick_level_choices(self) -> list[Upgrade]:
        """Pick three distinct upgrade choices with light contextual weighting."""
        weighted: list[Upgrade] = []
        for upgrade in UPGRADES:
            weight = 1
            if upgrade.key in {"damage", "projectiles", "speed"} and self.level <= 3:
                weight += 2
            if upgrade.key == "projectiles" and self.projectile_count >= 5:
                weight = 1
            if upgrade.key == "shield" and self.player_hp < self.player_max_hp * 0.45:
                weight += 2
            if upgrade.key == "pulse" and self.level >= 3:
                weight += 1
            if upgrade.key == "recovery" and self.level >= 4:
                weight += 1
            if upgrade.key == "pierce" and self.level >= 4:
                weight += 1
            if upgrade.key == "chain" and self.level >= 3:
                weight += 2
            if upgrade.key == "drone" and self.level >= 4:
                weight += 2
            if upgrade.key == "failsafe" and self.player_hp < self.player_max_hp * 0.55:
                weight += 2
            if upgrade.key == "overclock" and self.level >= 5:
                weight += 2
            weighted.extend([upgrade] * weight)

        choices: list[Upgrade] = []
        pool = weighted[:]
        while pool and len(choices) < 3:
            candidate = choice(pool)
            if candidate not in choices:
                choices.append(candidate)
            pool = [item for item in pool if item.key != candidate.key]

        while len(choices) < 3:
            fallback = choice(UPGRADES)
            if fallback not in choices:
                choices.append(fallback)

        return choices

    def current_run_evaluation(self) -> tuple[str, str, list[str]]:
        tags: list[str] = []
        if self.max_momentum >= 0.8:
            tags.append("High Momentum")
        if self.stats["deploys"] >= 3:
            tags.append("Deploy Focus")
        if self.stats["outages_resolved"] >= 1:
            tags.append("Boss Priority")
        if self.stats["failsafe_triggers"] >= 1:
            tags.append("Low HP Survivor")
        if self.drone_count >= 2:
            tags.append("Support Build")
        elif self.chain_count >= 2:
            tags.append("Chain Build")
        elif self.pulse_unlocked or self.overclock_level > 0:
            tags.append("Wave Cleaner")

        if self.stats["outages_resolved"] >= 2:
            return (
                "Outage Hunter",
                "You treated production outages as the main objective and kept the run under control.",
                tags[:2] or ["Boss Priority"],
            )
        if self.stats["deploys"] >= 4:
            return (
                "Deploy Specialist",
                "You kept rotating into risky deploy windows and turned map pressure into growth.",
                tags[:2] or ["Deploy Focus"],
            )
        if self.drone_count >= 2:
            return (
                "Pair Programming Lead",
                "This run leaned on support patches and felt more like coordinated repair work.",
                tags[:2] or ["Support Build"],
            )
        if self.chain_count >= 2 and (self.pierce > 0 or self.overclock_level > 0):
            return (
                "Code Review Machine",
                "One patch kept turning into more fixes as the build spread through clustered problems.",
                tags[:2] or ["Chain Build"],
            )
        if self.stats["failsafe_triggers"] >= 2 or (
            self.stats["failsafe_triggers"] >= 1 and self.time_survived >= 240
        ):
            return (
                "Last-Minute Hero",
                "This run survived repeated emergencies and kept shipping patches after near collapses.",
                tags[:2] or ["Low HP Survivor"],
            )
        if self.max_momentum >= 0.85 and self.stats["deploys"] >= 2:
            return (
                "Patch Sprinter",
                "You kept the run moving, stayed in flow, and converted mobility into steady growth.",
                tags[:2] or ["High Momentum"],
            )
        if (
            self.stats["bugs_fixed"] + self.stats["alerts_silenced"] + self.stats["scope_trimmed"] >= 90
            and (self.pulse_unlocked or self.overclock_level > 0)
        ):
            return (
                "Incident Cleaner",
                "The build focused on cleaning waves quickly instead of only escaping them.",
                tags[:2] or ["Wave Cleaner"],
            )
        return (
            "Steady Maintainer",
            "You kept the system running without overcommitting to a single high-risk route.",
            tags[:2] or ["Balanced Run"],
        )

    def unlock_achievement(self, key: str) -> None:
        entry = self.progression["achievements"].get(key)
        if entry is None or entry.get("unlocked"):
            return
        entry["unlocked"] = True
        self.new_achievements.append(key)
        self.spawn_floating_text(
            self.player_x - 36,
            self.player_y - 82,
            ACHIEVEMENT_DEFS.get(key, key),
            ACCENT,
        )

    def finalize_run_progression(self) -> None:
        totals = self.progression["totals"]
        totals["bugs_fixed"] += self.stats["bugs_fixed"]
        totals["meetings_dodged"] += self.stats["meetings_dodged"]
        totals["alerts_silenced"] += self.stats["alerts_silenced"]
        totals["scope_trimmed"] += self.stats["scope_trimmed"]
        totals["outages_resolved"] += self.stats["outages_resolved"]
        totals["deploys"] += self.stats["deploys"]
        totals["runs_played"] += 1
        totals["best_time"] = max(float(totals["best_time"]), self.time_survived, self.best_time)

        if self.selected_difficulty == "crunch" and self.time_survived >= 600:
            self.unlock_achievement("crunch_survivor")
        if self.stats["deploys"] >= 5:
            self.unlock_achievement("deploy_addict")
        if self.drone_count >= 2:
            self.unlock_achievement("pair_flow")
        if self.max_chain_hits >= 3:
            self.unlock_achievement("review_cascade")
        if totals["bugs_fixed"] >= 500:
            self.unlock_achievement("bug_tracker")

        save_progression(self.best_time, self.progression)

    def achievement_progress_text(self, key: str) -> str:
        totals = self.progression["totals"]
        if key == "crunch_survivor":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            if self.selected_difficulty == "crunch":
                return f"{min(self.time_survived, 600):0.0f}/600s"
            return "0/600s"
        if key == "deploy_addict":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(self.stats['deploys'], 5)}/5 in one run"
        if key == "pair_flow":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(self.drone_count, 2)}/2 pairs"
        if key == "review_cascade":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(self.max_chain_hits, 3)}/3 hits"
        if key == "bug_tracker":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(totals['bugs_fixed'], 500)}/500"
        return "Done" if self.progression["achievements"][key].get("unlocked") else "Not yet"

    def achievement_progress_ratio(self, key: str) -> float:
        totals = self.progression["totals"]
        if self.progression["achievements"][key].get("unlocked"):
            return 1.0
        if key == "crunch_survivor":
            if self.selected_difficulty != "crunch":
                return 0.0
            return min(1.0, self.time_survived / 600.0)
        if key == "deploy_addict":
            return min(1.0, self.stats["deploys"] / 5.0)
        if key == "pair_flow":
            return min(1.0, self.drone_count / 2.0)
        if key == "review_cascade":
            return min(1.0, self.max_chain_hits / 3.0)
        if key == "bug_tracker":
            return min(1.0, totals["bugs_fixed"] / 500.0)
        return 0.0

    def achievement_is_recent(self, key: str) -> bool:
        return key in self.new_achievements

    def next_achievement_hint(self) -> tuple[str, str] | None:
        locked = []
        for _, _, _, rows in ACHIEVEMENT_GROUPS:
            for key, description in rows:
                if not self.progression["achievements"][key].get("unlocked"):
                    locked.append((self.achievement_progress_ratio(key), key, description))
        if not locked:
            return None
        locked.sort(reverse=True)
        _, key, description = locked[0]
        return (ACHIEVEMENT_DEFS[key], description)

    def draw(self) -> None:
        shake_x = 0
        shake_y = 0
        if self.shake_timer > 0 and self.shake_strength > 0:
            shake_x = int((random() - 0.5) * 2 * self.shake_strength)
            shake_y = int((random() - 0.5) * 2 * self.shake_strength)

        self.screen.fill(BG)
        self.draw_grid()
        self.draw_objective()
        self.draw_hazards()

        if self.level_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((110, 78, 255, int(90 * self.level_flash)))
            self.screen.blit(overlay, (0, 0))
        elif self.hit_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((190, 42, 42, int(120 * self.hit_flash)))
            self.screen.blit(overlay, (0, 0))
        elif self.kill_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 176, 60, int(70 * self.kill_flash)))
            self.screen.blit(overlay, (0, 0))

        for shard in self.xp_shards:
            pygame.draw.circle(self.screen, XP_COLOR, (int(shard["x"]), int(shard["y"])), 6)

        self.draw_powerups()
        self.draw_drones()

        for projectile in self.projectiles:
            pygame.draw.circle(
                self.screen,
                projectile.get("color", PROJECTILE_COLOR),
                (int(projectile["x"]), int(projectile["y"])),
                int(projectile["radius"]),
            )

        for enemy in self.enemies:
            pygame.draw.circle(
                self.screen,
                enemy["type"].color,
                (int(enemy["x"]), int(enemy["y"])),
                int(enemy["type"].radius),
            )
            if enemy.get("elite"):
                pygame.draw.circle(
                    self.screen,
                    ACCENT,
                    (int(enemy["x"]), int(enemy["y"])),
                    int(enemy["type"].radius + 6),
                    2,
                )
            if enemy["type"].name == "Meeting":
                pygame.draw.circle(
                    self.screen,
                    (230, 240, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    6,
                )
            elif enemy["type"].name == "Alert":
                pygame.draw.circle(
                    self.screen,
                    (255, 233, 205),
                    (int(enemy["x"]), int(enemy["y"])),
                    4,
                )
                if enemy.get("dash_timer", 0) > 0:
                    pygame.draw.circle(
                        self.screen,
                        (255, 255, 255),
                        (int(enemy["x"]), int(enemy["y"])),
                        int(enemy["type"].radius + 4),
                        2,
                    )
            elif enemy["type"].name == "Scope Creep":
                pygame.draw.circle(
                    self.screen,
                    (245, 228, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    5,
                )
            elif enemy["type"].name == "Outage":
                pygame.draw.circle(
                    self.screen,
                    PANEL,
                    (int(enemy["x"]), int(enemy["y"])),
                    12,
                )
                pygame.draw.circle(
                    self.screen,
                    TEXT,
                    (int(enemy["x"]), int(enemy["y"])),
                    6,
                    2,
                )
                if enemy.get("rage"):
                    pygame.draw.circle(
                        self.screen,
                        RED,
                        (int(enemy["x"]), int(enemy["y"])),
                        int(enemy["type"].radius + 10),
                        2,
                    )
            elif enemy["type"].name == "Bugling":
                pygame.draw.circle(
                    self.screen,
                    (255, 248, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    3,
                )

        self.draw_player()
        if self.grace_timer > 0:
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (int(self.player_x), int(self.player_y)),
                int(self.player_radius + 6),
                2,
            )
        if self.pulse_unlocked:
            pygame.draw.circle(
                self.screen,
                (111, 82, 255),
                (int(self.player_x), int(self.player_y)),
                int(self.effective_pickup_radius() * 0.35),
                2,
            )

        self.draw_hud()
        self.draw_floating_texts()

        if self.state == "title":
            self.draw_title_overlay()
        elif self.state == "achievements":
            self.draw_achievements_overlay()
        elif self.state == "level_up":
            self.draw_level_up_overlay()
        elif self.state == "paused":
            self.draw_paused_overlay()
        elif self.state == "game_over":
            self.draw_game_over_overlay()

        if shake_x or shake_y:
            shaken = self.screen.copy()
            self.screen.fill(BG)
            self.screen.blit(shaken, (shake_x, shake_y))

    def draw_player(self) -> None:
        """Render a readable little developer character without sprite assets."""
        skin = self.current_skin()
        x = int(self.player_x)
        y = int(self.player_y)
        lean_x = int(self.player_dx * 4)
        lean_y = int(self.player_dy * 3)

        shadow = pygame.Rect(x - 18, y + 24, 36, 9)
        pygame.draw.ellipse(self.screen, (8, 10, 14), shadow)

        left_leg = pygame.Rect(x - 11 + lean_x, y + 14, 8, 18)
        right_leg = pygame.Rect(x + 3 + lean_x, y + 14, 8, 18)
        pygame.draw.rect(self.screen, (63, 92, 145), left_leg, border_radius=4)
        pygame.draw.rect(self.screen, (63, 92, 145), right_leg, border_radius=4)

        body = pygame.Rect(x - 15 + lean_x, y - 4 + lean_y, 30, 27)
        pygame.draw.rect(self.screen, skin["body"], body, border_radius=9)
        pygame.draw.rect(self.screen, skin["outline"], body, 2, border_radius=9)

        pygame.draw.line(self.screen, skin["arms"], (x - 13, y + 3), (x - 24, y + 12), 4)
        pygame.draw.line(self.screen, skin["arms"], (x + 13, y + 3), (x + 24, y + 12), 4)

        pygame.draw.circle(self.screen, skin["skin"], (x + lean_x, y - 20 + lean_y), 13)
        pygame.draw.arc(
            self.screen,
            skin["hair"],
            (x - 12 + lean_x, y - 32 + lean_y, 24, 16),
            pi,
            pi * 2,
            5,
        )
        pygame.draw.circle(self.screen, TEXT, (x - 5 + lean_x, y - 22 + lean_y), 2)
        pygame.draw.circle(self.screen, TEXT, (x + 5 + lean_x, y - 22 + lean_y), 2)
        pygame.draw.arc(
            self.screen,
            (87, 58, 35),
            (x - 7 + lean_x, y - 21 + lean_y, 14, 12),
            0,
            pi,
            2,
        )

        laptop = pygame.Rect(x - 21, y + 5, 42, 19)
        pygame.draw.rect(self.screen, PANEL, laptop, border_radius=4)
        pygame.draw.rect(self.screen, ACCENT, laptop, 2, border_radius=4)
        self.blit(self.small_font, "</>", skin["screen"], x - 17, y + 5)
        pygame.draw.line(self.screen, MUTED, (x - 24, y + 27), (x + 24, y + 27), 4)

    def draw_grid(self) -> None:
        for x in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

    def draw_hazards(self) -> None:
        if not self.hazards:
            return

        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for hazard in self.hazards:
            center = (int(hazard["x"]), int(hazard["y"]))
            radius = int(hazard["radius"])
            if hazard["warn"] > 0:
                alpha = 80 + int(70 * min(1.0, hazard["warn"]))
                pygame.draw.circle(surface, (255, 75, 75, alpha), center, radius, 3)
                pygame.draw.circle(surface, (255, 75, 75, 42), center, max(8, radius - 14), 2)
            else:
                pygame.draw.circle(surface, (190, 35, 35, 64), center, radius)
                pygame.draw.circle(surface, (255, 95, 85, 180), center, radius, 3)
        self.screen.blit(surface, (0, 0))

    def draw_powerups(self) -> None:
        for powerup in self.powerups:
            x = int(powerup["x"])
            y = int(powerup["y"])
            radius = int(powerup["radius"])
            color = powerup["color"]
            pygame.draw.circle(self.screen, color, (x, y), radius)
            pygame.draw.circle(self.screen, TEXT, (x, y), radius, 2)

            if powerup["kind"] == "heal":
                pygame.draw.ellipse(self.screen, PANEL, (x - 7, y - 8, 14, 18), 2)
                pygame.draw.arc(self.screen, TEXT, (x - 5, y - 13, 10, 10), pi, pi * 2, 2)
                pygame.draw.line(self.screen, TEXT, (x - 6, y - 2), (x + 6, y - 2), 2)
            elif powerup["kind"] == "bomb":
                pygame.draw.circle(self.screen, RED, (x, y), 8)
                self.blit(self.small_font, "{}", TEXT, x - 10, y - 10)
                pygame.draw.line(self.screen, TEXT, (x + 4, y - 10), (x + 10, y - 16), 2)
            elif powerup["kind"] == "haste":
                points = [(x - 7, y - 10), (x + 3, y - 2), (x - 2, y), (x + 8, y + 10)]
                pygame.draw.lines(self.screen, TEXT, False, points, 3)

    def draw_drones(self) -> None:
        if self.drone_count <= 0:
            return
        for index in range(self.drone_count):
            angle = self.time_survived * 2.4 + index * (2 * pi / max(1, self.drone_count))
            x = int(self.player_x + cos(angle) * 34)
            y = int(self.player_y + sin(angle) * 34)
            pygame.draw.circle(self.screen, BLUE, (x, y), 8)
            pygame.draw.circle(self.screen, TEXT, (x, y), 8, 2)
            pygame.draw.line(self.screen, TEXT, (x - 4, y), (x + 4, y), 2)
            pygame.draw.line(self.screen, TEXT, (x, y - 4), (x, y + 4), 2)

    def draw_objective(self) -> None:
        if self.objective is None:
            return

        objective = self.objective
        center = (int(objective["x"]), int(objective["y"]))
        radius = int(objective["radius"])
        progress = max(0.0, min(1.0, objective["progress"] / objective["required"]))
        ttl_ratio = max(0.0, min(1.0, objective["ttl"] / 16.0))
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        pygame.draw.circle(surface, (93, 201, 136, 32), center, radius)
        pygame.draw.circle(surface, (93, 201, 136, 150), center, radius, 3)
        pygame.draw.circle(surface, (255, 177, 66, 180), center, max(4, int(radius * progress)))
        pygame.draw.circle(surface, (19, 22, 29, 210), center, 14)
        pygame.draw.circle(surface, (239, 242, 248, 230), center, 5)

        timer_width = int(radius * 2 * ttl_ratio)
        timer_rect = pygame.Rect(center[0] - radius, center[1] + radius + 10, timer_width, 6)
        pygame.draw.rect(surface, (93, 201, 136, 190), timer_rect, border_radius=999)
        self.screen.blit(surface, (0, 0))

        label = f"Deploy {int(progress * 100)}%"
        self.blit(self.small_font, label, GREEN, center[0] - 44, center[1] - radius - 30)

    def draw_hud(self) -> None:
        panel = pygame.Rect(18, 18, 410, 184)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=16)

        self.blit(self.large_font, TITLE, TEXT, 28, 24)
        self.blit(self.small_font, f"Time  {self.time_survived:05.1f}s", TEXT, 28, 80)
        self.blit(self.small_font, f"Level {self.level}", TEXT, 28, 106)
        self.blit(self.small_font, f"Best  {self.best_time:05.1f}s", MUTED, 160, 106)
        self.blit(self.small_font, self.current_phase().name, ACCENT, 260, 80)
        self.blit(self.small_font, self.current_difficulty().label, MUTED, 260, 106)
        if self.current_phase().name == "Alert Storm":
            self.blit(self.small_font, "Pager noise rising", RED, 380, 106)
        if self.crisis_banner_timer > 0:
            self.blit(self.font, self.crisis_name, RED, 500, 28)
        outage = next((enemy for enemy in self.enemies if enemy["type"].name == "Outage"), None)
        if outage is not None:
            ratio = max(0.0, min(1.0, outage["hp"] / outage.get("max_hp", outage["hp"])))
            self.draw_bar(500, 58, 260, 12, ratio, OUTAGE_COLOR, "Outage")

        hp_ratio = max(0.0, self.player_hp / self.player_max_hp)
        xp_ratio = max(0.0, min(1.0, self.xp / self.xp_to_level))

        self.draw_bar(
            28,
            138,
            300,
            14,
            hp_ratio,
            RED,
            f"HP {int(self.player_hp)}/{int(self.player_max_hp)}",
        )
        self.draw_bar(28, 164, 300, 14, xp_ratio, BLUE, "Insight")
        self.draw_bar(28, 190, 300, 14, self.momentum, GREEN, f"Momentum {self.momentum_tier}")

        self.blit(self.small_font, "Move: WASD / Arrows", MUTED, 960, 24)
        self.blit(self.small_font, "Upgrades: 1 / 2 / 3", MUTED, 960, 48)
        self.blit(self.small_font, "Pause: P", MUTED, 960, 72)
        self.blit(self.small_font, "Exit: Esc", MUTED, 960, 96)
        if self.regen_interval > 0:
            self.blit(self.small_font, f"Regen {self.regen_interval:0.1f}s", MUTED, 960, 120)
        if self.pierce > 0:
            self.blit(self.small_font, f"Pierce {self.pierce}", MUTED, 960, 144)
        if self.focus_timer > 0:
            self.blit(self.small_font, f"Focus {self.focus_timer:0.1f}s", GREEN, 960, 168)
        if self.haste_timer > 0:
            self.blit(self.small_font, f"CI Boost {self.haste_timer:0.1f}s", BLUE, 960, 192)
        if self.momentum_tier != "Idle":
            self.blit(
                self.small_font,
                f"{self.momentum_tier}: Insight x{self.xp_multiplier():0.2f}",
                GREEN,
                960,
                216,
            )
        if self.drone_count > 0:
            self.blit(self.small_font, f"Pairs {self.drone_count}", MUTED, 960, 240)
        if self.chain_count > 0:
            self.blit(self.small_font, f"Code Review {self.chain_count}", MUTED, 960, 264)
        if self.failsafe_level > 0:
            cooldown = "ready" if self.failsafe_cooldown <= 0 else f"{self.failsafe_cooldown:0.1f}s"
            self.blit(self.small_font, f"Guard {cooldown}", MUTED, 960, 288)
        if self.overclock_level > 0:
            self.blit(self.small_font, f"Overclock {self.overclock_level}", MUTED, 960, 312)
        if self.objective is not None:
            objective_y = 82 if outage is not None else 58
            self.blit(self.small_font, "Optional: hold deploy window", GREEN, 500, objective_y)

    def draw_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        ratio: float,
        color: tuple[int, int, int],
        label: str,
    ) -> None:
        pygame.draw.rect(self.screen, GRID, (x, y, width, height), border_radius=999)
        pygame.draw.rect(self.screen, color, (x, y, width * ratio, height), border_radius=999)
        self.blit(self.small_font, label, TEXT, x + width + 12, y - 2)

    def draw_title_overlay(self) -> None:
        self.draw_overlay_panel(180, 130, 920, 460)
        self.blit(self.large_font, "Deadline Survivors", TEXT, 248, 180)
        self.blit(self.font, "Ship patches before bugs and deadlines take over.", MUTED, 248, 252)
        self.blit(self.font, "Pick difficulty: 1 Casual, 2 Normal, 3 Crunch", ACCENT, 248, 288)
        difficulty = self.current_difficulty()
        self.blit(
            self.font,
            f"Current: {difficulty.label} - {difficulty.description}",
            TEXT,
            248,
            326,
        )
        skin = self.current_skin()
        self.blit(
            self.font,
            f"Skin: {skin['label']} ({len(self.unlocked_skins())}/{len(PLAYER_SKINS)} unlocked) - press S",
            GREEN,
            248,
            352,
        )
        lines = [
            "Move constantly. Your developer ships patches automatically.",
            "Keep momentum for better rewards.",
            "Capture deploy windows for Focus mode.",
            "Pick up Coffee Breaks, Refactor Bombs, and CI Boosts.",
            "Red deadline zones punish standing still.",
            "Collect insight shards to level up.",
            "Pick upgrades with 1, 2, or 3.",
            "Press A to view local achievements.",
            "Press S to cycle unlocked skins.",
            "Press Space to start the run.",
        ]
        for index, line in enumerate(lines):
            self.blit(self.font, f"• {line}", TEXT, 248, 384 + index * 24)

    def draw_achievements_overlay(self) -> None:
        self.draw_overlay_panel(120, 70, 1040, 580)
        self.blit(self.large_font, "Achievements", TEXT, 170, 118)

        achievements = self.progression["achievements"]
        totals = self.progression["totals"]
        unlocked_count = sum(1 for value in achievements.values() if value.get("unlocked"))
        completion_ratio = unlocked_count / max(1, len(ACHIEVEMENT_DEFS))
        self.blit(
            self.font,
            f"Unlocked {unlocked_count}/{len(ACHIEVEMENT_DEFS)}",
            ACCENT,
            170,
            178,
        )
        self.blit(
            self.large_font,
            f"{int(completion_ratio * 100)}%",
            GREEN if completion_ratio >= 1.0 else TEXT,
            980,
            108,
        )
        self.blit(self.small_font, "Progress", MUTED, 1006, 168)
        self.blit(
            self.small_font,
            f"Runs {totals['runs_played']}  |  Best {float(totals['best_time']):05.1f}s  |  Bugs fixed {totals['bugs_fixed']}",
            MUTED,
            170,
            214,
        )
        self.draw_bar(170, 236, 240, 10, completion_ratio, GREEN, "Completion")
        next_hint = self.next_achievement_hint()
        if next_hint is not None:
            hint_title, hint_description = next_hint
            self.blit(self.small_font, f"Next target: {hint_title}", GREEN, 470, 236)
            self.blit(self.small_font, hint_description, MUTED, 470, 260)
        else:
            self.blit(self.small_font, "All current achievements unlocked.", GREEN, 470, 236)

        group_positions = [(160, 280), (610, 280), (160, 470), (610, 470)]
        for index, (group_name, group_color, group_description, rows) in enumerate(ACHIEVEMENT_GROUPS):
            group_x, group_y = group_positions[index]
            group_rect = pygame.Rect(group_x, group_y, 410, 150)
            pygame.draw.rect(self.screen, PANEL, group_rect, border_radius=16)
            pygame.draw.rect(self.screen, group_color, (group_x, group_y, 410, 6), border_radius=16)
            pygame.draw.rect(self.screen, GRID, group_rect, 2, border_radius=16)
            pygame.draw.circle(self.screen, group_color, (group_x + 18, group_y + 22), 7)
            self.blit(self.font, group_name, group_color, group_x + 34, group_y + 12)

            unlocked_in_group = sum(1 for key, _ in rows if achievements[key].get("unlocked"))
            self.blit(
                self.small_font,
                f"{unlocked_in_group}/{len(rows)} unlocked",
                MUTED,
                group_x + 270,
                group_y + 16,
            )
            self.blit(self.small_font, group_description, MUTED, group_x + 14, group_y + 40)

            for row_index, (key, description) in enumerate(rows):
                unlocked = achievements[key].get("unlocked", False)
                recent = self.achievement_is_recent(key)
                row_y = group_y + 62 + row_index * 24
                marker_color = ACCENT if recent else (GREEN if unlocked else GRID)
                pygame.draw.circle(self.screen, marker_color, (group_x + 16, row_y + 8), 6)
                self.blit(
                    self.small_font,
                    ACHIEVEMENT_DEFS[key],
                    TEXT if unlocked or recent else MUTED,
                    group_x + 30,
                    row_y - 2,
                )
                progress_ratio = self.achievement_progress_ratio(key)
                progress_text = self.achievement_progress_text(key)
                self.blit(
                    self.small_font,
                    progress_text,
                    marker_color if unlocked or recent else MUTED,
                    group_x + 286,
                    row_y - 2,
                )
                progress_bar_rect = pygame.Rect(group_x + 30, row_y + 16, 220, 6)
                pygame.draw.rect(self.screen, GRID, progress_bar_rect, border_radius=999)
                pygame.draw.rect(
                    self.screen,
                    GREEN if unlocked else ACCENT,
                    (progress_bar_rect.x, progress_bar_rect.y, int(progress_bar_rect.width * progress_ratio), progress_bar_rect.height),
                    border_radius=999,
                )
                wrapped = wrap_text(self.small_font, description, 150)
                if wrapped:
                    self.blit(self.small_font, wrapped[0], MUTED, group_x + 260, row_y + 10)
                if recent:
                    self.blit(self.small_font, "NEW", ACCENT, group_x + 236, row_y - 2)

        self.blit(self.small_font, "Press A or Backspace to return.", ACCENT, 170, 610)

    def draw_paused_overlay(self) -> None:
        self.draw_overlay_panel(260, 180, 760, 280)
        self.blit(self.large_font, "Paused", TEXT, 360, 245)
        self.blit(self.font, "Press P to continue the deploy.", TEXT, 360, 330)
        self.blit(self.font, "Use Esc if you want to quit the run.", MUTED, 360, 375)

    def draw_floating_texts(self) -> None:
        for item in self.floating_texts:
            alpha = max(0, min(255, int(255 * min(1.0, item["ttl"] / 0.7))))
            surface = self.small_font.render(item["text"], True, item["color"])
            surface.set_alpha(alpha)
            self.screen.blit(surface, (item["x"], item["y"]))

    def draw_level_up_overlay(self) -> None:
        self.draw_overlay_panel(140, 120, 1000, 480)
        self.blit(self.large_font, "New Insight", TEXT, 200, 170)
        self.blit(self.font, "Choose one developer upgrade.", MUTED, 200, 235)

        for index, upgrade in enumerate(self.level_choices):
            rect = pygame.Rect(190 + index * 300, 290, 260, 220)
            pygame.draw.rect(self.screen, PANEL, rect, border_radius=18)
            pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=18)
            self.blit(self.large_font, str(index + 1), ACCENT, rect.x + 20, rect.y + 14)
            self.blit(self.font, upgrade.name, TEXT, rect.x + 20, rect.y + 84)
            wrapped = wrap_text(self.small_font, upgrade.description, 220)
            for line_index, line in enumerate(wrapped):
                self.blit(self.small_font, line, MUTED, rect.x + 20, rect.y + 132 + line_index * 24)

    def draw_game_over_overlay(self) -> None:
        self.draw_overlay_panel(180, 120, 920, 470)
        title, description, tags = self.current_run_evaluation()
        self.blit(self.large_font, "Deploy Failed", TEXT, 300, 230)
        self.blit(
            self.font,
            f"Kept production alive for {self.time_survived:05.1f}s",
            TEXT,
            300,
            292,
        )
        self.blit(self.font, f"Best run {self.best_time:05.1f} seconds", MUTED, 300, 326)
        self.blit(self.font, f"Run evaluation: {title}", ACCENT, 300, 362)
        wrapped = wrap_text(self.small_font, description, 720)
        for index, line in enumerate(wrapped[:2]):
            self.blit(self.small_font, line, MUTED, 300, 396 + index * 22)
        if tags:
            self.blit(self.small_font, "Tags: " + "  |  ".join(tags), GREEN, 300, 444)
        if self.new_achievements:
            unlocked_names = [ACHIEVEMENT_DEFS.get(key, key) for key in self.new_achievements[:2]]
            self.blit(
                self.small_font,
                "Unlocked: " + "  |  ".join(unlocked_names),
                ACCENT,
                300,
                466,
            )
        stats = [
            f"Difficulty: {self.current_difficulty().label}",
            f"Insight: {int(self.stats['insight'])}",
            f"Bugs fixed: {self.stats['bugs_fixed']}",
            f"Meetings dodged: {self.stats['meetings_dodged']}",
            f"Alerts silenced: {self.stats['alerts_silenced']}",
            f"Scope trimmed: {self.stats['scope_trimmed']}",
            f"Outages resolved: {self.stats['outages_resolved']}",
            f"Deploys: {self.stats['deploys']}",
            f"Powerups used: {self.stats['powerups']}",
        ]
        for index, line in enumerate(stats):
            column_x = 300 if index < 5 else 640
            row_y = 492 + (index % 5) * 22
            self.blit(self.small_font, line, TEXT, column_x, row_y)
        self.blit(self.small_font, "Press A to view achievements.", GREEN, 640, 602 - 78)
        self.blit(self.small_font, "1 Casual  2 Normal  3 Crunch", ACCENT, 300, 532 + 70)
        self.blit(self.font, "Press Space to restart.", TEXT, 300, 567 + 40 - 10)

    def draw_overlay_panel(self, x: int, y: int, width: int, height: int) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        pygame.draw.rect(self.screen, PANEL, (x, y, width, height), border_radius=22)
        pygame.draw.rect(self.screen, ACCENT, (x, y, width, height), 2, border_radius=22)

    def blit(
        self,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        self.screen.blit(font.render(text, True, color), (x, y))


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def main() -> int:
    try:
        game = Game()
    except pygame.error as exc:
        print(f"Failed to start Deadline Survivors: {exc}", file=sys.stderr)
        return 1

    return game.run()
