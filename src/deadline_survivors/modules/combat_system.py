"""Combat, enemy resolution, projectiles, XP shards, and powerups."""

from __future__ import annotations

from math import atan2, cos, dist, pi, sin
from random import choice, random

from ..combat import fix_label_for_enemy, insight_value_for_enemy, stat_key_for_enemy
from ..constants import ACCENT, BLUE, GREEN, HEIGHT, OUTAGE_COLOR, PURPLE, RED, WIDTH, XP_COLOR
from ..content import ENEMY_TYPES
from ..models import EnemyState, EnemyType, ProjectileState
from ..state_factory import make_enemy_state, make_hazard, make_projectile


class CombatMixin:
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
                make_projectile(
                    self.player_x,
                    self.player_y,
                    cos(angle) * self.projectile_speed,
                    sin(angle) * self.projectile_speed,
                    self.projectile_damage
                    * damage_multiplier
                    * self.momentum_damage_multiplier(),
                    self.projectile_radius(),
                    self.projectile_color(),
                    self.pierce,
                    "player",
                    self.chain_count,
                    self.chain_range,
                )
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
        theme_color = self.current_patch_theme()["color"]
        if self.momentum_tier == "Overdrive":
            return self.mix_color(theme_color, GREEN, 0.72)
        if self.momentum_tier == "Flow":
            return self.mix_color(theme_color, ACCENT, 0.4)
        return theme_color

    def mix_color(
        self,
        base: tuple[int, int, int],
        accent: tuple[int, int, int],
        ratio: float,
    ) -> tuple[int, int, int]:
        ratio = max(0.0, min(1.0, ratio))
        return tuple(
            int(base[index] * (1.0 - ratio) + accent[index] * ratio) for index in range(3)
        )

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
        projectile: ProjectileState,
        source_enemy: EnemyState,
        spawned_projectiles: list[ProjectileState],
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
            make_projectile(
                source_enemy["x"],
                source_enemy["y"],
                cos(angle) * self.projectile_speed * 1.04,
                sin(angle) * self.projectile_speed * 1.04,
                projectile["damage"] * 0.82,
                max(4, projectile["radius"] - 1),
                PURPLE,
                0,
                "chain",
                max(0, remaining_chain),
                projectile.get("chain_range", self.chain_range),
                chain_hits,
            )
        )
        self.spawn_floating_text(source_enemy["x"], source_enemy["y"] - 26, "review", PURPLE)

    def find_chain_target(self, source_enemy: EnemyState, max_range: float) -> EnemyState | None:
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

    def trigger_overclock_burst(
        self,
        projectile: ProjectileState,
        source_enemy: EnemyState,
    ) -> None:
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
                self.resolve_enemy(enemy)
                self.kill_flash = 0.18
            else:
                alive.append(enemy)

        self.enemies = alive

    def resolve_enemy(
        self,
        enemy: EnemyState,
        insight_multiplier: float = 1.0,
        allow_powerup_drop: bool = True,
        allow_split: bool = True,
    ) -> None:
        """Apply all rewards and side effects for a truly defeated enemy."""
        self.drop_enemy_insight(enemy, insight_multiplier)
        self.spawn_fix_text(enemy)
        if allow_powerup_drop:
            self.maybe_drop_powerup(enemy)
        self.track_enemy_resolution(enemy)
        if allow_split and enemy["type"].name == "Scope Creep" and enemy.get("split_depth", 0) > 0:
            self.spawn_scope_split(enemy)

    def enemy_insight_value(self, enemy: EnemyState) -> float:
        """Return the base insight reward for resolving each enemy type."""
        return insight_value_for_enemy(enemy["type"].name)

    def drop_enemy_insight(self, enemy: EnemyState, multiplier: float = 1.0) -> None:
        """Drop an insight shard at an enemy position."""
        self.xp_shards.append(
            {
                "x": enemy["x"],
                "y": enemy["y"],
                "value": self.enemy_insight_value(enemy) * multiplier,
            }
        )

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

    def spawn_fix_text(self, enemy: EnemyState) -> None:
        self.spawn_floating_text(
            enemy["x"] - enemy["type"].radius,
            enemy["y"] - enemy["type"].radius - 10,
            fix_label_for_enemy(enemy["type"].name),
            XP_COLOR,
        )

    def track_enemy_resolution(self, enemy: EnemyState) -> None:
        stat_key = stat_key_for_enemy(enemy["type"].name)
        if stat_key is not None:
            self.stats[stat_key] += 1
        if enemy["type"].name == "Outage":
            self.unlock_achievement("first_outage")

    def maybe_drop_powerup(self, enemy: EnemyState) -> None:
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

    def advance_enemy(self, enemy: EnemyState, dt: float) -> None:
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

    def advance_outage(self, enemy: EnemyState, dt: float) -> None:
        enemy_type = enemy["type"]
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

    def emit_outage_wave(self, enemy: EnemyState) -> None:
        self.trigger_screen_shake(0.1, 2.6)
        self.spawn_floating_text(enemy["x"] - 18, enemy["y"] - 52, "Incident wave", OUTAGE_COLOR)
        for index in range(6):
            angle = index * (2 * pi / 6)
            radius = 54.0
            x = max(radius, min(WIDTH - radius, enemy["x"] + cos(angle) * 92))
            y = max(radius, min(HEIGHT - radius, enemy["y"] + sin(angle) * 92))
            self.hazards.append(
                make_hazard(
                    x,
                    y,
                    radius,
                    0.85,
                    1.2,
                    12.0 if not enemy["rage"] else 16.0,
                )
            )

    def summon_outage_support(self, enemy: EnemyState) -> None:
        alert = next(enemy_type for enemy_type in ENEMY_TYPES if enemy_type.name == "Alert")
        bug = next(enemy_type for enemy_type in ENEMY_TYPES if enemy_type.name == "Bug")
        self.spawn_floating_text(enemy["x"] - 26, enemy["y"] - 28, "Escalation", ACCENT)
        self.add_enemy(alert, elite=False, near_player=True)
        self.add_enemy(choice([alert, bug]), elite=False, near_player=True)

    def projectile_damage_multiplier(self) -> float:
        if self.projectile_count <= 1:
            return 1.0
        return max(0.45, 1.0 - (self.projectile_count - 1) * 0.18)

    def spawn_scope_split(self, enemy: EnemyState) -> None:
        for offset in (-16, 16):
            self.enemies.append(
                make_enemy_state(
                    EnemyType("Bugling", 12, 122, 16, 8, (218, 170, 255), 0.0),
                    enemy["x"] + offset,
                    enemy["y"] - offset * 0.25,
                    (
                        16 + self.time_survived * 0.18
                    ) * self.current_difficulty().enemy_hp_mult,
                    8 * self.current_difficulty().enemy_damage_mult,
                    99.0,
                    0,
                    False,
                )
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

    def run_scaling_bonus(self) -> float:
        """Scale some rewards gently so late-run tools keep pace with pressure."""
        return 1.0 + min(0.45, max(0, self.level - 1) * 0.035)

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
        scaling = self.run_scaling_bonus()
        handlers = {
            "heal": self.apply_heal_powerup,
            "bomb": self.apply_bomb_powerup,
            "haste": self.apply_haste_powerup,
        }
        handler = handlers.get(kind)
        if handler:
            handler(scaling)

    def apply_heal_powerup(self, scaling: float) -> None:
        heal_amount = 28.0 * scaling
        recovered = min(heal_amount, self.player_max_hp - self.player_hp)
        self.player_hp = min(self.player_max_hp, self.player_hp + heal_amount)
        self.play_sound("pickup")
        self.spawn_floating_text(
            self.player_x,
            self.player_y - 44,
            f"Coffee +{int(recovered)} HP",
            GREEN,
        )

    def apply_bomb_powerup(self, scaling: float) -> None:
        defeated = self.damage_enemies_with_bomb(92.0 * scaling, scaling)
        self.kill_flash = 0.6
        self.play_sound("crisis")
        self.trigger_screen_shake(0.2, 5.5)
        self.spawn_floating_text(
            self.player_x,
            self.player_y - 52,
            f"Refactor x{defeated}",
            ACCENT,
        )

    def damage_enemies_with_bomb(self, bomb_damage: float, scaling: float) -> int:
        defeated = 0
        survivors = []
        for enemy in self.enemies:
            enemy["hp"] -= bomb_damage
            if enemy["hp"] <= 0:
                defeated += 1
                self.resolve_enemy(
                    enemy,
                    0.7 * scaling,
                    allow_powerup_drop=False,
                    allow_split=False,
                )
            else:
                survivors.append(enemy)
                if enemy["type"].name == "Outage":
                    self.spawn_floating_text(
                        enemy["x"] - 28,
                        enemy["y"] - 52,
                        "Outage damaged",
                        ACCENT,
                    )
        self.enemies = survivors
        return defeated

    def apply_haste_powerup(self, scaling: float) -> None:
        self.haste_timer = min(12.0, 7.0 * scaling)
        self.play_sound("pickup")
        self.spawn_floating_text(self.player_x, self.player_y - 44, "CI Boost", BLUE)


