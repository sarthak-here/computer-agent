import json
from pathlib import Path
from datetime import datetime

from task_memory import TaskMemory


class Memory:
    def __init__(self, session_file: str = "session.json"):
        self.path = Path(session_file)
        self.history: list[dict] = []
        self.goal: str = ""
        self.start_time = datetime.now().isoformat()
        self.task_memory = TaskMemory()

    def add(self, action: dict):
        self.history.append({**action, "_step": len(self.history) + 1})

    def get_task_context(self) -> str:
        """Return cross-session context relevant to the current goal."""
        return self.task_memory.get_context(self.goal)

    def save(self, status: str = "completed", provider: str = ""):
        data = {
            "goal": self.goal,
            "start_time": self.start_time,
            "end_time": datetime.now().isoformat(),
            "steps": len(self.history),
            "history": self.history,
        }
        self.path.write_text(json.dumps(data, indent=2))
        print(f"\n💾 Session saved to {self.path}")

        # Phase 11: persist to cross-session task memory
        self.task_memory.record_session(
            goal=self.goal,
            provider=provider,
            steps=len(self.history),
            status=status,
            history=self.history,
        )

    def summary(self) -> str:
        lines = [f"Goal: {self.goal}", f"Steps taken: {len(self.history)}"]
        for a in self.history[-3:]:
            lines.append(f"  • {a.get('type')} — {a.get('reasoning', '')[:60]}")
        stats = self.task_memory.get_stats()
        lines.append(f"\n📚 Overall: {stats}")
        return "\n".join(lines)
