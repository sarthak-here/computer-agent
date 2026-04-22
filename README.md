# Computer-Using Agent (CUA)

> An AI that sees your screen and controls your computer — autonomously.

---

## What We're Building

A fully autonomous **Computer-Using Agent** that can take any high-level goal like:

> *"Open Chrome, go to Gmail, and draft an email to my boss saying I'll be late"*

...and actually do it — by seeing your screen, reasoning about what to click/type next, and executing actions in a loop until the goal is done.

No hardcoded scripts. No browser automation APIs. Just vision + reasoning + control.

This is the same class of technology being built by OpenAI (Operator), Anthropic (Claude computer use), and Google DeepMind — except this is open, runs with any LLM, and you control it.

### Full Vision (Roadmap)

```
Screen → Vision Model → Reasoning → Action → Feedback → Repeat
```

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Screen capture + base64 encoding | ✅ Done |
| 2 | Vision LLM understands screen content | ✅ Done |
| 3 | JSON action planning (click, type, scroll, hotkey) | ✅ Done |
| 4 | Action execution via pyautogui | ✅ Done |
| 5 | Closed feedback loop (act → re-capture → re-plan) | ✅ Done |
| 6 | Safety layer (dangerous action blocking + confirmation) | ✅ Done |
| 7 | Session memory + action history logging | ✅ Done |
| 8 | Multi-provider support (10 cloud APIs + local models) | ✅ Done |
| 9 | Local model support (Ollama, LM Studio, llama.cpp) | ✅ Done |
| 10 | UI element detection (OpenCV + optional YOLO) | ✅ Done |
| 11 | Multi-step task memory across sessions | ✅ Done |
| 12 | Web UI / dashboard to watch the agent live | ✅ Done |
| 13 | Voice goal input ("Hey agent, do this...") | ✅ Done |
| 14 | Full auto mode with rollback on failure | ✅ Done |

---

## What We've Built (Current MVP)

### Architecture

```
main.py              ← orchestrates the loop + all CLI flags
providers.py         ← unified interface for all LLM providers
screen_capture.py    ← grabs a screenshot, converts to base64
planner.py           ← sends screenshot to chosen LLM, gets next action as JSON
executor.py          ← executes click/type/key/scroll, safety checks
memory.py            ← logs every step to a timestamped JSON session file
task_memory.py       ← cross-session memory: past goals, patterns, app notes  [Phase 11]
detector.py          ← OpenCV + optional YOLO UI element detection             [Phase 10]
dashboard.py         ← Flask/SocketIO real-time web dashboard                  [Phase 12]
voice.py             ← microphone goal input via Whisper / Google STT          [Phase 13]
rollback.py          ← state checkpoints + Ctrl+Z rollback on failure          [Phase 14]
```

### How It Works

1. You give the agent a goal in plain English and pick a provider
2. Agent captures your screen as a PNG
3. Screenshot + goal is sent to the vision LLM of your choice
4. LLM returns the single next action as JSON (e.g. `{"type": "click", "x": 540, "y": 300}`)
5. Action is executed on your computer
6. Screen is captured again — loop continues until goal is done or max steps hit

### Safety

- **Supervised mode** (default): confirms every action before executing
- **Dangerous action detection**: blocks anything containing `delete`, `format`, `shutdown`, etc.
- **Emergency stop**: move mouse to top-left corner of screen instantly kills the agent
- **Max steps limit**: agent stops after N actions to prevent runaway loops

---

## Supported Providers

| Provider | Default Model | Vision | Env Key |
|----------|--------------|--------|---------|
| `anthropic` | claude-sonnet-4-6 | ✅ | `ANTHROPIC_API_KEY` |
| `openai` | gpt-4o | ✅ | `OPENAI_API_KEY` |
| `gemini` | gemini-1.5-pro | ✅ | `GEMINI_API_KEY` |
| `groq` | llama-3.2-90b-vision-preview | ✅ | `GROQ_API_KEY` |
| `mistral` | pixtral-12b-2409 | ✅ | `MISTRAL_API_KEY` |
| `together` | Llama-3.2-90B-Vision-Instruct-Turbo | ✅ | `TOGETHER_API_KEY` |
| `ollama` | llava | ✅ | none (local) |
| `lmstudio` | local-model | ✅ | none (local) |
| `llamacpp` | local-model | ✅ | none (local) |
| `azure` | gpt-4o | ✅ | `AZURE_OPENAI_API_KEY` |
| `deepseek` | deepseek-chat | ❌ text only | `DEEPSEEK_API_KEY` |
| `cohere` | command-r-plus | ❌ text only | `COHERE_API_KEY` |

Run `python main.py --list-providers` to see this table anytime.

---

## Local Models (No API Key Needed)

Run the agent fully offline using locally downloaded models like **Llama 3**, **Gemma**, **Mistral**, **LLaVA**, etc.

### Option 1 — Ollama (easiest)

```bash
# Install Ollama from https://ollama.com
ollama pull llava                  # vision model (sees the screen)
ollama pull llama3.2-vision        # newer, better vision
ollama pull gemma3                 # Gemma 3 (Google)
ollama pull mistral                # Mistral 7B
```

```bash
python main.py --goal "open notepad" --provider ollama --model llava
python main.py --goal "open notepad" --provider ollama --model llama3.2-vision
python main.py --goal "open notepad" --provider ollama --model gemma3
```

### Option 2 — LM Studio (GUI, easiest for Windows)

1. Download [LM Studio](https://lmstudio.ai)
2. Search and download any model (LLaVA, Gemma, Mistral, Llama...)
3. Go to **Local Server** tab → Start server
4. Run:

```bash
python main.py --goal "open notepad" --provider lmstudio --model your-model-name
```

### Option 3 — llama.cpp server

```bash
# Start server with a vision model
./server -m llava-v1.6.gguf --mmproj mmproj-llava.gguf -ngl 99 --port 8080

python main.py --goal "open notepad" --provider llamacpp
```

---

## Logging

Every session is logged in real time to the `logs/` folder.

```
logs/
  agent.log          ← master log, every session ever (append-only)
  1713456789.log     ← per-session log (one file per run)
```

Each log records exactly what the agent did, step by step:

```
[2026-04-18 14:32:01] ============================================================
[2026-04-18 14:32:01] SESSION START  2026-04-18 14:32:01
[2026-04-18 14:32:01] Session ID : 1713456789
[2026-04-18 14:32:01] Goal       : Open Notepad and type Hello World
[2026-04-18 14:32:01] Provider   : anthropic  |  Model: claude-sonnet-4-6
[2026-04-18 14:32:01] ============================================================
[2026-04-18 14:32:03] CAPTURE    : step 1, screen size 1920x1080
[2026-04-18 14:32:03] LLM CALL   : anthropic / claude-sonnet-4-6
[2026-04-18 14:32:04] LLM RESP   : {"type": "hotkey", "keys": ["win", "r"], "reasoning": "Open Run dialog"}
[2026-04-18 14:32:04] STEP 1
[2026-04-18 14:32:04]   Action   : hotkey
[2026-04-18 14:32:04]   Keys     : win + r
[2026-04-18 14:32:04]   Reason   : Open Run dialog to launch Notepad
[2026-04-18 14:32:06] CAPTURE    : step 2, screen size 1920x1080
...
[2026-04-18 14:32:18] SESSION END  |  status=completed  |  total_steps=4
```

Blocked/denied actions are also logged:
```
[2026-04-18 14:35:01]   BLOCKED  : user denied -> {"type": "click", ...}
```

To watch a session live as it runs:
```bash
# Windows (PowerShell)
Get-Content logs\agent.log -Wait

# Mac/Linux
tail -f logs/agent.log
```

---

## Setup

```bash
git clone https://github.com/sarthak-here/computer-agent
cd computer-agent

# Install all dependencies (or just the ones for your provider)
pip install -r requirements.txt
```

Set your API key for whichever provider you use:

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...
set OPENAI_API_KEY=sk-...
set GEMINI_API_KEY=AI...
set GROQ_API_KEY=gsk_...
set MISTRAL_API_KEY=...

# Mac/Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

Local providers (Ollama, LM Studio, llama.cpp) need no API key — just start the local server.

---

## Usage

```bash
# Interactive — picks provider, asks for goal
python main.py

# With a specific provider
python main.py --goal "open Notepad and write Hello World"
python main.py --goal "..." --provider openai
python main.py --goal "..." --provider gemini --model gemini-1.5-flash
python main.py --goal "..." --provider groq
python main.py --goal "..." --provider ollama --model llava
python main.py --goal "..." --provider lmstudio --model your-model

# See all providers
python main.py --list-providers

# Auto mode — no confirmation per step (be careful)
python main.py --goal "..." --auto

# Limit steps
python main.py --goal "..." --max-steps 10

# Phase 10 — UI element detection (OpenCV finds buttons/inputs, passes coords to LLM)
python main.py --goal "..." --detect

# Phase 12 — Live web dashboard at http://127.0.0.1:7860
python main.py --goal "..." --dashboard

# Phase 13 — Voice goal input (speak instead of type)
python main.py --voice

# Phase 14 — Auto-rollback on failure (Ctrl+Z chain + clipboard restore)
python main.py --goal "..." --rollback

# Combine flags
python main.py --voice --detect --dashboard --rollback --auto
```

---

## New Features (Phases 10–14)

### Phase 10 — UI Element Detection (`--detect`)

Runs OpenCV edge/contour detection on every screenshot to find interactive elements (buttons, inputs, toolbars). Detected coordinates are injected into the LLM prompt so it can click more accurately. Optionally drops in a YOLO model (`models/yolo_ui.pt`) for higher accuracy — no YOLO model is required, OpenCV is the default.

```bash
python main.py --goal "click the Submit button" --detect
```

### Phase 11 — Cross-Session Task Memory (automatic)

`task_memory.json` is written after every session. Future sessions for similar goals automatically receive:
- A list of past attempts and their outcomes
- Per-app notes you can add manually
- The key action sequence from the best matching past success

No extra flag needed — memory loads automatically at startup.

### Phase 12 — Live Web Dashboard (`--dashboard`)

Opens `http://127.0.0.1:7860` in your browser. Shows:
- Live compressed screenshots updated every step
- Real-time action log (step type, reasoning, blocked/done events)
- Session metadata (provider, model, step counter)

```bash
python main.py --goal "open gmail and draft an email" --dashboard
```

### Phase 13 — Voice Goal Input (`--voice`)

Press ENTER to activate the microphone, then speak your goal. Uses Whisper (offline, more accurate) if available, falls back to Google STT.

```bash
python main.py --voice
# then press ENTER and speak: "Open Chrome and search for cat videos"
```

Install deps: `pip install SpeechRecognition pyaudio`
For offline Whisper: `pip install openai-whisper`

### Phase 14 — Rollback on Failure (`--rollback`)

Before each state-modifying action (type, hotkey, press), the agent snapshots clipboard contents and the active window title. If the planner errors or the action fails, it fires a `Ctrl+Z` chain (up to 5 undos) and restores the clipboard. The rollback log is printed in the session summary.

```bash
python main.py --goal "edit the document" --rollback
```

### Example Goals That Work

- `"Open Notepad and type a grocery list"`
- `"Open Chrome and search for latest AI news"`
- `"Open the calculator and compute 1234 * 5678"`
- `"Go to github.com and search for computer vision repos"`

---

## Demo

```
🎯 Goal: Open Notepad and type Hello World
🤖 Provider: Anthropic  |  Model: claude-sonnet-4-6
🔒 Mode: SUPERVISED (confirm each step)
───────────────────────────────────────────────────────

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
- Windows / Mac / Linux with a display
- One of: an API key for a cloud provider, OR a local model running via Ollama/LM Studio/llama.cpp

```
# Core (always required)
mss, pyautogui, pillow

# Providers (install only what you use)
anthropic                  # Anthropic Claude
openai                     # OpenAI, Azure, Ollama, LM Studio, llama.cpp, DeepSeek
google-generativeai        # Google Gemini
groq                       # Groq
mistralai                  # Mistral AI
together                   # Together AI
cohere                     # Cohere

# Phase 10 — UI detection
opencv-python              # always available, no model needed
ultralytics                # optional: YOLO (needs models/yolo_ui.pt)

# Phase 12 — Dashboard
flask, flask-socketio

# Phase 13 — Voice input
SpeechRecognition, pyaudio
openai-whisper             # optional: offline transcription

# Phase 14 — Rollback
pyperclip, pygetwindow
```

---

## Why This Is Different

Most automation tools (Selenium, Playwright, AutoHotkey) require you to know the app's internal structure — DOM elements, window handles, API hooks.

This agent works like a human — it **just looks at the screen** and figures it out. That means it works on **any app, any website, any window**, without any integration. And now it works with **any LLM** — cloud or fully local.

---

## Contributing

PRs welcome. Especially interested in:
- UI element detection to improve click accuracy
- Voice input for goal setting
- A web dashboard to watch the agent live
- Support for more local model backends

---

## Disclaimer

This tool controls your mouse and keyboard. Use responsibly. Always run in supervised mode first. The authors are not responsible for unintended actions taken by the agent.
