"""
Phase 14: Rollback on failure.
Snapshots state before risky actions and attempts recovery when errors occur.

Strategy:
  1. Before each state-modifying action, checkpoint clipboard + active window.
  2. On error/failure, fire Ctrl+Z chain to undo recent changes.
  3. Restore clipboard to pre-action value.
  4. Log all rollback events for session review.
"""
from __future__ import annotations
import time
from datetime import datetime


class RollbackManager:
    UNDO_STEPS = 5
    RISKY_TYPES = {"type", "press", "hotkey"}

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.checkpoints: list[dict] = []
        self.rollback_log: list[dict] = []

    def checkpoint(self, step: int, action: dict, screenshot=None) -> dict:
        """Save a state snapshot before an action is executed."""
        cp = {
            "step": step,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "clipboard": self._get_clipboard(),
            "active_window": self._get_active_window(),
        }
        if screenshot:
            cp["screenshot_size"] = list(screenshot.size)
        self.checkpoints = (self.checkpoints + [cp])[-10:]
        return cp

    def rollback(self, reason: str = "error", dashboard_emit=None) -> bool:
        """
        Attempt to undo the last action.
        Returns True if rollback was attempted.
        """
        if not self.checkpoints:
            return False

        cp = self.checkpoints[-1]
        print(f"\n🔄 Rollback triggered ({reason}) — step {cp['step']}")

        if dashboard_emit:
            dashboard_emit("rollback", {"reason": reason, "step": cp["step"]})

        success = self._undo_chain()

        if cp.get("clipboard") is not None:
            self._restore_clipboard(cp["clipboard"])

        self.rollback_log.append({
            "step": cp["step"],
            "action": cp["action"],
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "success": success,
        })

        if success:
            print("✅ Rollback applied — verify screen before continuing")
        else:
            print("⚠️  Rollback attempted (partial) — check screen manually")

        return True

    def should_checkpoint(self, action: dict) -> bool:
        """Returns True if this action type warrants a pre-execution checkpoint."""
        atype = action.get("type", "")
        if atype in self.RISKY_TYPES:
            return True
        if atype == "hotkey":
            keys = [k.lower() for k in action.get("keys", [])]
            return any(k in {"delete", "backspace", "d", "x", "z"} for k in keys)
        return False

    def summary(self) -> str:
        if not self.rollback_log:
            return "No rollbacks triggered."
        lines = [f"Rollbacks: {len(self.rollback_log)}"]
        for r in self.rollback_log:
            status = "ok" if r["success"] else "partial"
            lines.append(f"  Step {r['step']}: {r['reason']} ({status})")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _undo_chain(self) -> bool:
        try:
            import pyautogui
            for _ in range(self.UNDO_STEPS):
                pyautogui.hotkey("ctrl", "z")
                time.sleep(0.2)
            return True
        except Exception:
            return False

    def _get_clipboard(self) -> str | None:
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            return None

    def _restore_clipboard(self, content: str):
        try:
            import pyperclip
            pyperclip.copy(content)
        except Exception:
            pass

    def _get_active_window(self) -> str | None:
        try:
            import pygetwindow as gw
            w = gw.getActiveWindow()
            return w.title if w else None
        except Exception:
            return None
