# Computer-Using Agent (CUA)

> An AI that sees your screen and controls your computer — autonomously.

---

## What We're Building

A fully autonomous **Computer-Using Agent** that can take any high-level goal like:

> *"Open Chrome, go to Gmail, and draft an email to my boss saying I'll be late"*

...and actually do it — by seeing your screen, reasoning about what to click/type next, and executing actions in a loop until the goal is done.

No hardcoded scripts. No browser automation APIs. Just vision + reasoning + control.

This is the same class of technology being built by OpenAI (Operator), Anthropic (Claude computer use), and Google DeepMind — except this runs locally, is open, and you control it.

### Full Vision (Roadmap)

```
Screen → Vision Model → Reasoning → Action → Feedback → Repeat
```

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Screen capture + base64 encoding | ✅ Done |
| 2 | Claude vision understands screen content | ✅ Done |
| 3 | JSON action planning (click, type, scroll, hotkey) | ✅ Done |
| 4 | Action execution via pyautogui | ✅ Done |
| 5 | Closed feedback loop (act → re-capture → re-plan) | ✅ Done |
| 6 | Safety layer (dangerous action blocking + confirmation) | ✅ Done |
| 7 | Session memory + action history logging | ✅ Done |
| 8 | UI element detection (YOLO-based button finding) | 🔜 Planned |
| 9 | Multi-step task memory across sessions | 🔜 Planned |
| 10 | Web UI / dashboard to watch the agent live | 🔜 Planned |
| 11 | Voice goal input ("Hey agent, do this...") | 🔜 Planned |
| 12 | Full auto mode with rollback on failure | 🔜 Planned |

---

## What We've Built (Current MVP)

### Architecture

```
main.py              ← orchestrates the loop
screen_capture.py    ← grabs a screenshot, converts to base64
planner.py           ← sends screenshot to Claude, gets next action as JSON
executor.py          ← executes click/type/key/scroll, safety checks
memory.py            ← logs every step to a timestamped JSON session file
```

### How It Works

1. You give the agent a goal in plain English
2. Agent captures your screen
3. Screenshot is sent to **Claude claude-sonnet-4-6** (vision model)
4. Claude returns the single next action as JSON (e.g. `{"type": "click", "x": 540, "y": 300}`)
5. Action is executed on your computer
6. Screen is captured again — loop continues until goal is done or max steps hit

### Safety

- **Supervised mode** (default): confirms every action before executing
- **Dangerous action detection**: blocks anything containing `delete`, `format`, `shutdown`, etc.
- **Emergency stop**: move mouse to top-left corner of screen instantly kills the agent
- **Max steps limit**: agent stops after N actions to prevent runaway loops

---

## Setup

```bash
git clone https://github.com/sarthak-here/computer-agent
cd computer-agent

pip install -r requirements.txt
```

Set your Anthropic API key:

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# Mac/Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

```bash
# Interactive — it will ask you for a goal
python main.py

# Direct goal
python main.py --goal "open Notepad and write Hello World"

# Auto mode — no confirmation per step (be careful)
python main.py --goal "search for Python tutorials on Chrome" --auto

# Limit max steps
python main.py --goal "..." --max-steps 10
```

### Example Goals That Work

- `"Open Notepad and type a grocery list"`
- `"Take a screenshot and save it to the Desktop"`
- `"Open Chrome and go to github.com"`
- `"Open the calculator and compute 1234 * 5678"`

---

## Demo

```
🎯 Goal: Open Notepad and type Hello World
🔒 Mode: SUPERVISED (confirm each step)
──────────────────────────────────────────

[Step 1/15] Capturing screen...
🧠 Thinking...
💡 Decided: hotkey — Press Win+R to open Run dialog
🤖 Proposed action: {"type": "hotkey", "keys": ["win", "r"], ...}
Execute? [Y/n/s]: y

[Step 2/15] Capturing screen...
🧠 Thinking...
💡 Decided: type — Type 'notepad' in the Run dialog
...

✅ Agent says goal is complete!
💾 Session saved to session_1713456789.json
```

---

## Requirements

- Python 3.10+
- Anthropic API key (Claude claude-sonnet-4-6 with vision)
- Windows / Mac / Linux with a display

```
anthropic>=0.94.0
mss>=10.0.0
pyautogui>=0.9.54
pillow>=10.0.0
```

---

## Why This Is Different

Most automation tools (Selenium, Playwright, AutoHotkey) require you to know the app's internal structure — DOM elements, window handles, API hooks.

This agent works like a human — it **just looks at the screen** and figures it out. That means it works on any app, any website, any window, without any integration.

---

## Contributing

PRs welcome. Especially interested in:
- UI element detection to improve click accuracy
- Voice input for goal setting
- A web dashboard to watch the agent live
- Reliability improvements and error recovery

---

## Disclaimer

This tool controls your mouse and keyboard. Use responsibly. Always run in supervised mode first. The authors are not responsible for unintended actions taken by the agent.
