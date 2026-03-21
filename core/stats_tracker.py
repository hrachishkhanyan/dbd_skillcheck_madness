import json
import time
from dataclasses import dataclass, field


@dataclass
class StatsTracker:
    total: int = 0
    greats: int = 0
    goods: int = 0
    fails: int = 0
    misses: int = 0
    current_streak: int = 0
    best_streak: int = 0
    reaction_times: list = field(default_factory=list)
    history: list = field(default_factory=list)

    def record(self, result: str, reaction_time_ms: float):
        self.total += 1
        entry = {
            "result": result,
            "reaction_ms": round(reaction_time_ms, 1),
            "timestamp": time.time(),
        }
        self.history.append(entry)

        if result == "great":
            self.greats += 1
            self.current_streak += 1
            self.reaction_times.append(reaction_time_ms)
        elif result == "good":
            self.goods += 1
            self.current_streak += 1
            self.reaction_times.append(reaction_time_ms)
        elif result == "miss":
            self.misses += 1
            self.current_streak = 0
        else:  # fail
            self.fails += 1
            self.current_streak = 0

        self.best_streak = max(self.best_streak, self.current_streak)

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return ((self.greats + self.goods) / self.total) * 100

    @property
    def avg_reaction_ms(self) -> float:
        if not self.reaction_times:
            return 0.0
        return sum(self.reaction_times) / len(self.reaction_times)

    def reset(self):
        self.total = 0
        self.greats = 0
        self.goods = 0
        self.fails = 0
        self.misses = 0
        self.current_streak = 0
        self.best_streak = 0
        self.reaction_times.clear()
        self.history.clear()

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "greats": self.greats,
            "goods": self.goods,
            "fails": self.fails,
            "misses": self.misses,
            "best_streak": self.best_streak,
            "accuracy_pct": round(self.accuracy, 1),
            "avg_reaction_ms": round(self.avg_reaction_ms, 1),
            "history": self.history,
        }

    def export_json(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
