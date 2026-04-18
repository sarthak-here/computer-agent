import json
from pathlib import Path
from datetime import datetime


class Memory:
    def __init__(self, session_file: str = "session.json"):
        self.path = Path(session_file)
        self.history: list[dict] = []
        self.goal: str = ""
        self.start_time = datetime.now().isoformat()

    def add(self, action: dict):
        self.history.append({**action, "_step": len(self.history) + 1})

    def save(self):
        data = {
            "goal": self.goal,
            "start_time": self.start_time,
            "end_time": datetime.now().isoformat(),
            "steps": len(self.history),
            "history": self.history,
        }
        self.path.write_text(json.dumps(data, indent=2))
        print(f"\n💾 Session saved to {self.path}")

    def summary(self) -> str:
        if not self.history:
            return "No actions taken yet."
        lines = [f"Goal: {self.goal}", f"Steps taken: {len(self.history)}"]
        for a in self.history[-3:]:
            lines.append(f"  • {a.get('type')} — {a.get('reasoning', '')[:60]}")
        return "\n".join(lines)
