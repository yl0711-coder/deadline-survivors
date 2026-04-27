"""Encounter director, enemy spawning, bosses, hazards, and objectives."""

from __future__ import annotations

from math import cos, dist, pi, sin
from random import choice, random

from ..constants import GREEN, HEIGHT, RED, WIDTH, XP_COLOR
from ..content import ENEMY_TYPES, OUTAGE_BOSS
from ..encounters import enemy_spawn_pool
from ..models import EnemyType, ObjectiveState
from ..state_factory import make_enemy_state, make_hazard, make_outage_state


class DirectorMixin:
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

