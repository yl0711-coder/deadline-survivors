"""Achievements, run evaluation, and progression persistence hooks."""

from __future__ import annotations

from ..constants import ACCENT
from ..content import ACHIEVEMENT_DEFS, ACHIEVEMENT_GROUPS
from ..storage import save_progression


class AchievementSystemMixin:
    def current_run_evaluation(self) -> tuple[str, str, list[str]]:
        tags = self.current_run_tags()
        title, description, fallback_tags = self.current_run_evaluation_text()
        return title, description, tags[:2] or fallback_tags

    def current_run_tags(self) -> list[str]:
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
        return tags

    def current_run_evaluation_text(self) -> tuple[str, str, list[str]]:
        for matched, title, description, fallback_tags in self.run_evaluation_candidates():
            if matched:
                return title, description, fallback_tags
        return self.default_run_evaluation_text()

    def run_evaluation_candidates(self) -> list[tuple[bool, str, str, list[str]]]:
        return [
            self.outage_hunter_evaluation(),
            self.deploy_specialist_evaluation(),
            self.pair_programming_evaluation(),
            self.code_review_evaluation(),
            self.last_minute_evaluation(),
            self.patch_sprinter_evaluation(),
            self.incident_cleaner_evaluation(),
        ]

    def outage_hunter_evaluation(self) -> tuple[bool, str, str, list[str]]:
        if self.stats["outages_resolved"] >= 2:
            return (
                True,
                "Outage Hunter",
                "You treated production outages as the main objective and kept the run under control.",
                ["Boss Priority"],
            )
        return False, "", "", []

    def deploy_specialist_evaluation(self) -> tuple[bool, str, str, list[str]]:
        return (
            self.stats["deploys"] >= 4,
            "Deploy Specialist",
            "You kept rotating into risky deploy windows and turned map pressure into growth.",
            ["Deploy Focus"],
        )

    def pair_programming_evaluation(self) -> tuple[bool, str, str, list[str]]:
        return (
            self.drone_count >= 2,
            "Pair Programming Lead",
            "This run leaned on support patches and felt more like coordinated repair work.",
            ["Support Build"],
        )

    def code_review_evaluation(self) -> tuple[bool, str, str, list[str]]:
        return (
            self.chain_count >= 2 and (self.pierce > 0 or self.overclock_level > 0),
            "Code Review Machine",
            "One patch kept turning into more fixes as the build spread through clustered problems.",
            ["Chain Build"],
        )

    def last_minute_evaluation(self) -> tuple[bool, str, str, list[str]]:
        return (
            self.stats["failsafe_triggers"] >= 2
            or (self.stats["failsafe_triggers"] >= 1 and self.time_survived >= 240),
            "Last-Minute Hero",
            "This run survived repeated emergencies and kept shipping patches after near collapses.",
            ["Low HP Survivor"],
        )

    def patch_sprinter_evaluation(self) -> tuple[bool, str, str, list[str]]:
        return (
            self.max_momentum >= 0.85 and self.stats["deploys"] >= 2,
            "Patch Sprinter",
            "You kept the run moving, stayed in flow, and converted mobility into steady growth.",
            ["High Momentum"],
        )

    def incident_cleaner_evaluation(self) -> tuple[bool, str, str, list[str]]:
        return (
            self.run_resolved_count() >= 90 and (self.pulse_unlocked or self.overclock_level > 0),
            "Incident Cleaner",
            "The build focused on cleaning waves quickly instead of only escaping them.",
            ["Wave Cleaner"],
        )

    def default_run_evaluation_text(self) -> tuple[str, str, list[str]]:
        return (
            "Steady Maintainer",
            "You kept the system running without overcommitting to a single high-risk route.",
            ["Balanced Run"],
        )

    def run_resolved_count(self) -> int:
        """Return all enemy-pressure resolved during the current run."""
        return (
            self.stats["bugs_fixed"]
            + self.stats["meetings_dodged"]
            + self.stats["alerts_silenced"]
            + self.stats["scope_trimmed"]
            + self.stats["outages_resolved"]
        )

    def total_resolved_count(self) -> int:
        """Return all cumulative enemy-pressure resolved across saved runs."""
        totals = self.progression["totals"]
        return (
            totals["bugs_fixed"]
            + totals["meetings_dodged"]
            + totals["alerts_silenced"]
            + totals["scope_trimmed"]
            + totals["outages_resolved"]
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

        self.apply_run_based_achievement_checks(include_cumulative=True)

        save_progression(self.best_time, self.progression)

    def apply_run_based_achievement_checks(self, include_cumulative: bool) -> None:
        if self.selected_difficulty == "crunch" and self.time_survived >= 600:
            self.unlock_achievement("crunch_survivor")
        if self.stats["deploys"] >= 5:
            self.unlock_achievement("deploy_addict")
        if self.drone_count >= 2:
            self.unlock_achievement("pair_flow")
        if self.max_chain_hits >= 3:
            self.unlock_achievement("review_cascade")
        if include_cumulative and self.progression["totals"]["bugs_fixed"] >= 500:
            self.unlock_achievement("bug_tracker")

    def persist_progression_snapshot(self) -> None:
        self.best_time = max(self.best_time, self.time_survived)
        self.progression["totals"]["best_time"] = max(
            float(self.progression["totals"]["best_time"]),
            self.best_time,
        )
        self.apply_run_based_achievement_checks(include_cumulative=False)
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
