"""
Real-time activity logger.

Writes to two places simultaneously:
  logs/agent.log   — append-only master log (every session, forever)
  logs/<session>.log — per-session log (readable summary of one run)
"""

from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

MASTER_LOG = LOG_DIR / "agent.log"


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Logger:
    def __init__(self, session_id: str, goal: str, provider: str, model: str):
        self.session_id = session_id
        self.session_log = LOG_DIR / f"{session_id}.log"
        self._write_both(f"{'='*60}")
        self._write_both(f"SESSION START  {_ts()}")
        self._write_both(f"Session ID : {session_id}")
        self._write_both(f"Goal       : {goal}")
        self._write_both(f"Provider   : {provider}  |  Model: {model}")
        self._write_both(f"{'='*60}")

    def _write_both(self, line: str):
        stamped = f"[{_ts()}] {line}"
        with open(MASTER_LOG, "a", encoding="utf-8") as f:
            f.write(stamped + "\n")
        with open(self.session_log, "a", encoding="utf-8") as f:
            f.write(stamped + "\n")

    def step(self, step: int, action: dict):
        atype = action.get("type", "unknown")
        reason = action.get("reasoning", "")

        self._write_both(f"")
        self._write_both(f"STEP {step}")
        self._write_both(f"  Action   : {atype}")

        # Log specifics per action type
        if atype == "click":
            btn = action.get("button", "left")
            double = "double-" if action.get("double") else ""
            self._write_both(f"  Target   : {double}{btn}-click at ({action.get('x')}, {action.get('y')})")
        elif atype == "type":
            text = action.get("text", "")
            display = text if len(text) <= 80 else text[:77] + "..."
            self._write_both(f"  Text     : \"{display}\"")
        elif atype == "press":
            self._write_both(f"  Key      : {action.get('key')}")
        elif atype == "hotkey":
            self._write_both(f"  Keys     : {' + '.join(action.get('keys', []))}")
        elif atype == "scroll":
            self._write_both(f"  Scroll   : {action.get('clicks')} clicks at ({action.get('x')}, {action.get('y')})")
        elif atype == "wait":
            self._write_both(f"  Duration : {action.get('seconds')}s")
        elif atype == "done":
            self._write_both(f"  Status   : goal marked complete")

        self._write_both(f"  Reason   : {reason}")

    def blocked(self, action: dict, reason: str = "user denied"):
        self._write_both(f"  BLOCKED  : {reason} -> {action}")

    def error(self, msg: str):
        self._write_both(f"ERROR      : {msg}")

    def screen_capture(self, step: int, size: tuple):
        self._write_both(f"CAPTURE    : step {step}, screen size {size[0]}x{size[1]}")

    def llm_call(self, provider: str, model: str):
        self._write_both(f"LLM CALL   : {provider} / {model}")

    def llm_response(self, raw: str):
        preview = raw.replace("\n", " ")[:120]
        self._write_both(f"LLM RESP   : {preview}")

    def session_end(self, steps: int, status: str = "completed"):
        self._write_both(f"")
        self._write_both(f"SESSION END  |  status={status}  |  total_steps={steps}")
        self._write_both(f"Log saved  : {self.session_log}")
        self._write_both(f"{'='*60}\n")
        print(f"\n[log] Session log: {self.session_log}")
        print(f"[log] Master log : {MASTER_LOG}")
