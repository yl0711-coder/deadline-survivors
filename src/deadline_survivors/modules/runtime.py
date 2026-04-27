from __future__ import annotations

from math import atan2, cos, dist, hypot, pi, sin
from random import choice, random
import sys

import pygame

from ..audio import AudioPlayer
from ..content import (
    DIFFICULTIES,
    ENEMY_TYPES,
    OUTAGE_BOSS,
    PHASES,
)
from ..encounters import enemy_spawn_pool
from ..constants import (
    ACCENT,
    BLUE,
    FPS,
    GREEN,
    HEIGHT,
    PURPLE,
    RED,
    TITLE,
    WIDTH,
    XP_COLOR,
)
from ..models import (
    Difficulty,
    EnemyState,
    EnemyType,
    FloatingTextState,
    HazardState,
    InsightShardState,
    ObjectiveState,
    Phase,
    PowerupState,
    ProjectileState,
    Upgrade,
)
from ..state_factory import make_enemy_state, make_hazard, make_outage_state, make_projectile
from ..storage import load_best_time, load_progression, save_best_time
from . import input as input_module
from .combat_system import CombatMixin
from .progression import ProgressionMixin
from .renderer import RendererMixin


def create_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Create a bundled pygame font without querying platform font registries."""
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class Game(RendererMixin, ProgressionMixin, CombatMixin):
    def __init__(self) -> None:
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = create_font(24)
        self.small_font = create_font(18)
        self.large_font = create_font(52, bold=True)
        self.best_time = load_best_time()
        self.progression = load_progression()
        self.selected_difficulty = "normal"
        self.selected_skin = self.progression.get("selected_skin", "default")
        self.selected_badge = self.progression.get("selected_badge", "none")
        self.selected_patch_theme = self.progression.get("selected_patch_theme", "default")
        self.audio = AudioPlayer()
        self.fire_sound_timer = 0.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.menu_return_state = "title"
        self.title_menu_index = 0
        self.game_over_menu_index = 0
        self.help_scroll = 0
        self.reset()

    def reset(self) -> None:
        """Reset all run-local state before returning to title or starting."""
        self.reset_menu_state()
        self.reset_run_progress_state()
        self.reset_player_state()
        self.reset_combat_state()
        self.reset_director_state()
        self.reset_build_state()
        self.reset_feedback_state()
        self.reset_run_stats()
        self.reset_runtime_collections()

    def reset_menu_state(self) -> None:
        self.state = "title"
        self.menu_return_state = "title"
        self.help_scroll = 0
        self.game_over_menu_index = 0

    def reset_run_progress_state(self) -> None:
        self.time_survived = 0.0
        self.level = 1
        self.xp = 0.0
        self.xp_to_level = self.xp_required_for_level(self.level)

    def reset_player_state(self) -> None:
        self.player_x = WIDTH / 2
        self.player_y = HEIGHT / 2
        self.player_dx = 0.0
        self.player_dy = 0.0
        self.player_radius = 18
        self.player_speed = 265.0
        self.player_hp = 100.0
        self.player_max_hp = 100.0

    def reset_combat_state(self) -> None:
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

    def reset_director_state(self) -> None:
        self.crisis_timer = 24.0
        self.boss_timer = 52.0
        self.crisis_name = ""
        self.crisis_banner_timer = 0.0
        self.hazard_timer = 12.0
        self.objective_timer = 14.0
        self.objective: ObjectiveState | None = None
        self.objective_successes = 0

    def reset_build_state(self) -> None:
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

    def reset_feedback_state(self) -> None:
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.hit_flash = 0.0
        self.level_flash = 0.0
        self.kill_flash = 0.0
        self.death_burst_timer = 0.0
        self.death_burst_x = self.player_x
        self.death_burst_y = self.player_y

    def reset_run_stats(self) -> None:
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

    def reset_runtime_collections(self) -> None:
        self.new_achievements: list[str] = []
        self.floating_texts: list[FloatingTextState] = []
        self.enemies: list[EnemyState] = []
        self.projectiles: list[ProjectileState] = []
        self.xp_shards: list[InsightShardState] = []
        self.hazards: list[HazardState] = []
        self.powerups: list[PowerupState] = []
        self.level_choices: list[Upgrade] = []

    def start_run(self) -> None:
        self.reset()
        self.state = "playing"

    def current_difficulty(self) -> Difficulty:
        return next(
            difficulty for difficulty in DIFFICULTIES if difficulty.key == self.selected_difficulty
        )

    def play_sound(self, key: str) -> None:
        self.audio.play(key)

    def trigger_screen_shake(self, duration: float, strength: float) -> None:
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_strength = max(self.shake_strength, strength)

    def choose_upgrade(self, key: str) -> None:
        """Apply a run-long level-up upgrade."""
        scaling = self.run_scaling_bonus()
        handlers = {
            "damage": self.apply_damage_upgrade,
            "speed": self.apply_speed_upgrade,
            "projectiles": self.apply_projectiles_upgrade,
            "magnet": self.apply_magnet_upgrade,
            "shield": self.apply_shield_upgrade,
            "pierce": self.apply_pierce_upgrade,
            "pulse": self.apply_pulse_upgrade,
            "recovery": self.apply_recovery_upgrade,
            "chain": self.apply_chain_upgrade,
            "drone": self.apply_drone_upgrade,
            "failsafe": self.apply_failsafe_upgrade,
            "overclock": self.apply_overclock_upgrade,
        }
        handler = handlers.get(key)
        if handler:
            handler(scaling)
        self.play_sound("level")

    def apply_damage_upgrade(self, scaling: float) -> None:
        gain = int(8 * scaling)
        self.projectile_damage += gain
        self.spawn_floating_text(self.player_x, self.player_y - 44, f"+{gain} damage", ACCENT)

    def apply_speed_upgrade(self, scaling: float) -> None:
        del scaling
        self.player_speed *= 1.12 + min(0.07, (self.level - 1) * 0.006)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Move up", BLUE)

    def apply_projectiles_upgrade(self, scaling: float) -> None:
        del scaling
        if self.projectile_count < 5:
            self.projectile_count += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "+1 patch", PURPLE)
            return
        self.attack_cooldown *= 0.94
        self.projectile_damage += 2
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Multicast tuned", PURPLE)

    def apply_magnet_upgrade(self, scaling: float) -> None:
        self.pickup_radius += int(26 * scaling)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Radar up", XP_COLOR)

    def apply_shield_upgrade(self, scaling: float) -> None:
        max_hp_gain = int(24 * scaling)
        heal_gain = int(14 * scaling)
        self.player_max_hp += max_hp_gain
        self.player_hp = min(self.player_max_hp, self.player_hp + heal_gain)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Shield up", BLUE)

    def apply_pierce_upgrade(self, scaling: float) -> None:
        del scaling
        self.pierce += 1
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pierce +1", PURPLE)

    def apply_pulse_upgrade(self, scaling: float) -> None:
        self.pulse_unlocked = True
        self.pulse_timer = min(self.pulse_timer, 1.0)
        self.pulse_radius += int(22 * scaling)
        self.pulse_damage += int(8 * scaling)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pulse online", PURPLE)

    def apply_recovery_upgrade(self, scaling: float) -> None:
        del scaling
        self.regen_interval = (
            6.0 if self.regen_interval == 0 else max(2.7, self.regen_interval * 0.82)
        )
        self.regen_timer = self.regen_interval
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Recovery up", BLUE)

    def apply_chain_upgrade(self, scaling: float) -> None:
        del scaling
        self.chain_count += 1
        self.chain_range = 120 + self.chain_count * 20
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Code review", PURPLE)

    def apply_drone_upgrade(self, scaling: float) -> None:
        del scaling
        self.drone_count += 1
        self.drone_cooldown = max(0.34, self.drone_cooldown * 0.86)
        self.drone_timer = min(self.drone_timer, 0.35)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pair online", GREEN)

    def apply_failsafe_upgrade(self, scaling: float) -> None:
        del scaling
        self.failsafe_level += 1
        self.failsafe_cooldown = min(self.failsafe_cooldown, 3.0)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Guard armed", BLUE)

    def apply_overclock_upgrade(self, scaling: float) -> None:
        del scaling
        self.overclock_level += 1
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Build overclocked", ACCENT)

    def run(self) -> int:
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.persist_progression_snapshot()
                    return 0
                if event.type == pygame.KEYDOWN:
                    if self.handle_keydown(event.key):
                        return 0

            if self.state == "playing":
                self.update(dt)
            elif self.state == "game_over":
                self.update_game_over_effects(dt)

            self.draw()
            pygame.display.flip()

    def handle_keydown(self, key: int) -> bool:
        return input_module.handle_keydown(self, key)

    def handle_achievements_input(self, key: int) -> None:
        input_module.handle_achievements_input(self, key)

    def handle_info_input(self, key: int) -> None:
        input_module.handle_info_input(self, key)

    def handle_title_input(self, key: int) -> bool:
        return input_module.handle_title_input(self, key)

    def handle_shared_menu_input(self, key: int) -> bool:
        return input_module.handle_shared_menu_input(self, key)

    def handle_game_over_input(self, key: int) -> bool:
        return input_module.handle_game_over_input(self, key)

    def handle_level_up_input(self, key: int) -> None:
        input_module.handle_level_up_input(self, key)

    def pick_choice(self, index: int) -> None:
        input_module.pick_choice(self, index)

    def activate_title_menu_item(self) -> None:
        """Run the currently highlighted title-menu action."""
        input_module.activate_title_menu_item(self)

    def activate_game_over_menu_item(self) -> None:
        """Run the currently highlighted game-over action."""
        input_module.activate_game_over_menu_item(self)

    def update(self, dt: float) -> None:
        """Advance one gameplay frame while the run is active."""
        self.advance_frame_timers(dt)
        self.update_player_systems(dt)
        self.update_directors(dt)
        self.update_combat_systems(dt)
        self.finish_run_if_player_is_defeated()

    def advance_frame_timers(self, dt: float) -> None:
        """Advance short-lived gameplay timers for one active frame."""
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

    def update_player_systems(self, dt: float) -> None:
        """Update movement, build effects, and run objectives."""
        self.move_player(dt)
        self.update_momentum(dt)
        self.update_regen(dt)
        self.update_drone(dt)
        self.update_objective(dt)

    def update_directors(self, dt: float) -> None:
        """Update systems that add external pressure to the run."""
        self.update_crisis_director(dt)
        self.update_boss_director(dt)
        self.update_hazards(dt)
        self.spawn_enemy_if_ready()

    def spawn_enemy_if_ready(self) -> None:
        """Spawn the next enemy wave when the spawn timer expires."""
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            phase = self.current_phase()
            spawn_base = phase.spawn_base * self.current_difficulty().spawn_interval_mult
            self.spawn_timer = max(0.18, spawn_base - min(self.time_survived / 72, 0.18))

    def update_combat_systems(self, dt: float) -> None:
        """Update attacks, collisions, pickups, and floating combat feedback."""
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

    def finish_run_if_player_is_defeated(self) -> None:
        """Finalize a run exactly once when player health reaches zero."""
        if self.player_hp <= 0:
            self.state = "game_over"
            self.death_burst_timer = 1.0
            self.death_burst_x = self.player_x
            self.death_burst_y = self.player_y
            self.shake_timer = 0.0
            self.shake_strength = 0.0
            self.hit_flash = 0.0
            self.kill_flash = 0.0
            self.level_flash = 0.0
            self.floating_texts = []
            self.play_sound("fail")
            if self.time_survived > self.best_time:
                self.best_time = self.time_survived
                save_best_time(self.best_time)
            self.finalize_run_progression()

    def update_game_over_effects(self, dt: float) -> None:
        """Advance short-lived effects that remain visible after gameplay stops."""
        self.death_burst_timer = max(0.0, self.death_burst_timer - dt)

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

    def complete_objective(self, objective: ObjectiveState) -> None:
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
                make_projectile(
                    origin_x,
                    origin_y,
                    cos(shot_angle) * self.projectile_speed * 0.88,
                    sin(shot_angle) * self.projectile_speed * 0.88,
                    self.projectile_damage * damage_multiplier,
                    max(4, self.projectile_radius() - 1),
                    BLUE,
                    max(0, self.pierce - 1),
                    "drone",
                    max(0, self.chain_count - 1),
                    self.chain_range,
                )
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
        elite = self.should_spawn_elite(elite)
        x, y = self.enemy_spawn_position(near_player)
        hp = self.enemy_spawn_hp(enemy_type, elite)
        damage = enemy_type.damage * self.current_difficulty().enemy_damage_mult
        self.enemies.append(
            make_enemy_state(
                enemy_type,
                x,
                y,
                hp,
                damage,
                1.4 + random() * 0.9,
                self.enemy_split_depth(enemy_type),
                elite,
            )
        )

    def should_spawn_elite(self, elite: bool | None) -> bool:
        if elite is None:
            elite_chance = 0.0
            if self.level >= 8:
                elite_chance += 0.03
            if self.level >= 12:
                elite_chance += 0.05
            if self.current_phase().name == "Deadline Crunch":
                elite_chance += 0.04
            return random() < elite_chance
        return elite

    def enemy_spawn_position(self, near_player: bool) -> tuple[float, float]:
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
        return x, y

    def enemy_spawn_hp(self, enemy_type: EnemyType, elite: bool) -> float:
        level_pressure = max(0, self.level - 7) * 2.15
        elite_multiplier = 2.2 if elite else 1.0
        difficulty = self.current_difficulty()
        return (
            enemy_type.hp
            + level_pressure
            + self.time_survived * (0.35 + self.current_phase().pressure * 0.22)
        ) * difficulty.enemy_hp_mult * elite_multiplier

    def enemy_split_depth(self, enemy_type: EnemyType) -> int:
        return 1 if enemy_type.name == "Scope Creep" else 0

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
            make_outage_state(
                OUTAGE_BOSS,
                x,
                y,
                hp,
                OUTAGE_BOSS.damage * difficulty.enemy_damage_mult,
            )
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
            make_hazard(x, y, radius, 1.05, 1.65, damage)
        )

    def pick_enemy_type(self) -> EnemyType:
        return choice(enemy_spawn_pool(ENEMY_TYPES, self.current_phase().name))

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


def main() -> int:
    try:
        game = Game()
    except pygame.error as exc:
        print(f"Failed to start Deadline Survivors: {exc}", file=sys.stderr)
        return 1

    if "--smoke-test" in sys.argv:
        pygame.quit()
        return 0

    return game.run()
