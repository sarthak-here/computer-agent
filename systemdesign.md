# Computer Agent — System Design

## What It Does
An autonomous AI agent that takes a natural-language goal, captures your screen, and controls the computer (mouse, keyboard) in a loop until the goal is achieved. Supports 10 vision LLM providers including Claude, GPT-4o, Gemini, and local Ollama models.

---

## Architecture

```
User Goal (text / voice)
        |
        v
+-------------------------------------------------------+
|                     main.py                           |
|  +------------------------------------------------+   |
|  |           Agent Loop (max N steps)            |   |
|  |                                               |   |
|  |  screen_capture --> planner --> executor      |   |
|  |      |               |             |          |   |
|  |  Screenshot       LLM call     pyautogui      |   |
|  |  (PIL Image)    (vision API)  (click/type/key)|   |
|  |      |               |             |          |   |
|  |      +---------------+-------------+          |   |
|  |                   memory                      |   |
|  |              (session history)                |   |
|  +------------------------------------------------+   |
|                                                       |
|  Optional modules:                                    |
|  detector.py  -> OpenCV/YOLO UI element detection     |
|  rollback.py  -> Auto-undo on failure                 |
|  voice.py     -> Whisper speech-to-text input         |
|  dashboard.py -> Live web dashboard (Flask/SocketIO)  |
|  logger.py    -> Full session logging to JSON         |
+-------------------------------------------------------+
```

---

## Input

| Source | Detail |
|---|---|
| --goal "open notepad" | CLI flag |
| Interactive prompt | python main.py then type goal |
| --voice | Whisper transcribes spoken goal |
| --auto | Runs without per-step approval |

---

## Data Flow (one step of the agent loop)

```
Step 1 — screen_capture.py
  PIL screenshot of full desktop
  Resize + base64-encode for vision API

Step 2 — detector.py (optional, --detect flag)
  OpenCV edge detection -> contour bounding boxes
  Falls back to YOLO if model file present
  Returns: [{type, x, y, w, h, cx, cy}, ...]

Step 3 — planner.py
  Builds prompt: system_prompt + goal + action_history + screenshot
  Calls configured vision LLM provider
  Parses JSON response:
    {"type": "click", "x": 540, "y": 300, "reasoning": "..."}

Step 4 — executor.py
  Safety check: rejects actions containing "delete", "rm -rf", etc.
  User approval gate (bypassed with --auto)
  pyautogui dispatches: click / type / press / hotkey / scroll / wait

Step 5 — memory.py
  Appends action + screenshot + reasoning to session history
  task_memory.py: cross-session context persisted to JSON
  On completion: saves full session to session_<timestamp>.json

Step 6 — Loop
  Continue until planner returns {"type": "done"}
  OR max_steps reached
```

---

## Providers Supported

| Provider | Default Model | Notes |
|---|---|---|
| Anthropic | claude-sonnet-4-6 | Default |
| OpenAI | gpt-4o | |
| Gemini | gemini-1.5-flash | |
| Groq | llama-3.2-vision | Fastest inference |
| Ollama | llava / bakllava | 100% local, no API key |
| Azure / Mistral / Together / DeepSeek | various | |

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| JSON-only planner output | Structured actions are deterministic to execute; no free-text parsing |
| Dangerous action guard | Blocks rm -rf, shutdown, drop table before execution |
| Per-step screenshot | Screen state changes; stale context causes wrong coordinates |
| Cross-session TaskMemory | Agent learns from past runs, avoids repeating failed approaches |
| Provider abstraction | Single call_provider() function, swap LLM with one --provider flag |

---

## Interview Conclusion

This project implements the full perception-action loop of a computer-use agent: screenshot -> vision LLM -> structured action -> pyautogui execution -> repeat. The key technical challenge is grounding: the LLM must map high-level intent to pixel-precise coordinates on a live desktop. The optional UI element detector (OpenCV contour detection with YOLO fallback) injects detected button bounding boxes into the planner prompt, significantly improving click accuracy. The safety guard and per-step approval gate prevent unrecoverable actions. The provider abstraction makes the system model-agnostic — switching from Claude to a local Llama model is a single CLI flag, which matters for air-gapped or privacy-sensitive environments. The cross-session task memory is what separates this from a one-shot script: the agent remembers what worked and what failed.
