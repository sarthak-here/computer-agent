"""
Phase 11: Cross-session task memory.
Persists learned knowledge about goals, apps, and action patterns across sessions.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime


TASK_MEMORY_FILE = Path("task_memory.json")

_APP_KEYWORDS = {
    "notepad": "notepad", "chrome": "chrome", "firefox": "firefox",
    "calculator": "calculator", "excel": "excel", "word": "word",
    "gmail": "gmail", "github": "github", "vscode": "vscode",
    "terminal": "terminal", "cmd": "terminal", "powershell": "terminal",
    "explorer": "explorer", "settings": "settings",
}


class TaskMemory:
    """Persistent cross-session memory of goals, outcomes, and app behaviors."""

    def __init__(self, path: str | Path = TASK_MEMORY_FILE):
        self.path = Path(path)
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"sessions": [], "app_notes": {}, "goal_patterns": []}

    def save(self):
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def record_session(self, goal: str, provider: str, steps: int,
                       status: str, history: list[dict]):
        """Record a completed session for future reference."""
        apps = self._extract_apps(history)
        self._data["sessions"].append({
            "date": datetime.now().isoformat(),
            "goal": goal,
            "provider": provider,
            "steps": steps,
            "status": status,
            "apps": apps,
        })
        self._data["sessions"] = self._data["sessions"][-50:]

        if status == "completed":
            self._learn_pattern(goal, history, apps)

        self.save()

    def add_app_note(self, app: str, note: str):
        """Remember something about how a specific app behaves."""
        if app not in self._data["app_notes"]:
            self._data["app_notes"][app] = []
        self._data["app_notes"][app].append({
            "note": note,
            "date": datetime.now().isoformat(),
        })
        self.save()

    def get_context(self, goal: str) -> str:
        """Return relevant cross-session context for the current goal."""
        lines = []

        similar = self._find_similar_goals(goal)
        if similar:
            lines.append("Past similar tasks:")
            for s in similar[:3]:
                lines.append(
                    f"  • [{s['status']}] {s['goal']} "
                    f"({s['steps']} steps, {s['date'][:10]})"
                )

        for app in self._guess_apps(goal):
            notes = self._data["app_notes"].get(app, [])
            if notes:
                lines.append(f"Notes about {app}:")
                for n in notes[-3:]:
                    lines.append(f"  • {n['note']}")

        pattern = self._get_matching_pattern(goal)
        if pattern:
            lines.append("Previously successful approach for similar goal:")
            for i, a in enumerate(pattern[:5]):
                lines.append(
                    f"  Step {i+1}: {a.get('type')} — "
                    f"{str(a.get('reasoning', ''))[:60]}"
                )

        return "\n".join(lines)

    def get_stats(self) -> str:
        sessions = self._data["sessions"]
        if not sessions:
            return "No previous sessions."
        total = len(sessions)
        done = sum(1 for s in sessions if s["status"] == "completed")
        return (
            f"Sessions: {total} total, {done} completed "
            f"({100 * done // total}% success rate)"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_apps(self, history: list[dict]) -> list[str]:
        apps: set[str] = set()
        for action in history:
            text = json.dumps(action).lower()
            for kw, app in _APP_KEYWORDS.items():
                if kw in text:
                    apps.add(app)
        return list(apps)

    def _guess_apps(self, goal: str) -> list[str]:
        g = goal.lower()
        return [app for kw, app in _APP_KEYWORDS.items() if kw in g]

    def _find_similar_goals(self, goal: str) -> list[dict]:
        goal_words = set(goal.lower().split())
        scored = []
        for s in self._data["sessions"]:
            past = set(s["goal"].lower().split())
            overlap = len(goal_words & past) / max(len(goal_words), 1)
            if overlap > 0.3:
                scored.append((overlap, s))
        scored.sort(reverse=True)
        return [s for _, s in scored[:5]]

    def _learn_pattern(self, goal: str, history: list[dict], apps: list[str]):
        self._data["goal_patterns"].append({
            "goal": goal,
            "apps": apps,
            "key_actions": history[:10],
            "date": datetime.now().isoformat(),
        })
        self._data["goal_patterns"] = self._data["goal_patterns"][-20:]

    def _get_matching_pattern(self, goal: str) -> list[dict] | None:
        goal_words = set(goal.lower().split())
        for pattern in reversed(self._data["goal_patterns"]):
            past = set(pattern["goal"].lower().split())
            overlap = len(goal_words & past) / max(len(goal_words), 1)
            if overlap > 0.5:
                return pattern["key_actions"]
        return None
