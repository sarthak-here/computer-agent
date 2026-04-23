# Computer Agent - System Design

## What It Does
An autonomous AI agent that takes a natural-language goal, captures your screen,
and controls the computer (mouse + keyboard) in a loop until the goal is achieved.
Supports 10 vision LLM providers including Claude, GPT-4o, Gemini, and local Ollama.

---

## Architecture

```
User Goal (text / voice)
        |
        v
+-------------------------------------------------------+
|                     main.py                           |
|  +------------------------------------------------+   |
|  |          Agent Loop (max N steps)              |   |
|  |                                                |   |
|  |  screen_capture --> planner --> executor       |   |
|  |      |                |             |          |   |
|  |  Screenshot        LLM call    pyautogui       |   |
|  |  (PIL Image)    (vision API)  click/type/key   |   |
|  |      |                |             |          |   |
|  |      +----------------+-------------+          |   |
|  |                    memory                      |   |
|  |               (session history)                |   |
|  +------------------------------------------------+   |
|                                                       |
|  Optional modules:                                    |
|  detector.py  -> OpenCV/YOLO UI element detection     |
|  rollback.py  -> Auto-undo on failure                 |
|  voice.py     -> Whisper speech-to-text input         |
|  dashboard.py -> Live web dashboard (SocketIO)        |
|  logger.py    -> Full session logging to JSON         |
+-------------------------------------------------------+
```

---

## Input

| Source              | Detail                                    |
|---------------------|-------------------------------------------|
| --goal "open Chrome"| CLI flag                                  |
| Interactive prompt  | python main.py then type goal             |
| --voice             | Whisper transcribes spoken goal           |
| --auto              | Runs without per-step user approval       |

---

## Data Flow (one step of the agent loop)

```
Step 1 - screen_capture.py
  PIL screenshot of full desktop
  Resize + base64-encode for vision API

Step 2 - detector.py (optional, --detect flag)
  OpenCV edge detection -> contour bounding boxes
  Falls back to YOLO if model file present
  Returns: [{type, x, y, w, h, cx, cy}, ...]

Step 3 - planner.py
  Builds prompt: system_prompt + goal + history + screenshot
  Calls configured vision LLM provider
  Parses JSON response:
    {"type": "click", "x": 540, "y": 300, "reasoning": "..."}

Step 4 - executor.py
  Safety check: rejects actions with "delete", "rm -rf", "shutdown"
  User approval gate (bypassed with --auto)
  pyautogui dispatches: click / type / press / hotkey / scroll

Step 5 - memory.py
  Appends action + reasoning to session history
  task_memory.py: cross-session context persisted to JSON
  On end: saves full session to session_<timestamp>.json

Step 6 - Loop
  Continue until planner returns {"type": "done"}
  OR max_steps reached
```

---

## Providers Supported

| Provider   | Default Model        | Notes              |
|------------|----------------------|--------------------|
| Anthropic  | claude-sonnet-4-6    | Default            |
| OpenAI     | gpt-4o               |                    |
| Gemini     | gemini-1.5-flash     |                    |
| Groq       | llama-3.2-vision     | Fastest inference  |
| Ollama     | llava / bakllava     | 100% local, no key |
| Azure / Mistral / Together / DeepSeek | various | |

---

## Key Design Decisions

| Decision                   | Reason                                                  |
|----------------------------|---------------------------------------------------------|
| JSON-only planner output   | Structured actions are deterministic; no free-text parse|
| Dangerous action guard     | Blocks rm -rf, shutdown before they execute             |
| Per-step screenshot        | Screen state changes; stale context = wrong coordinates |
| Cross-session TaskMemory   | Agent learns from past runs, avoids repeating failures  |
| Provider abstraction       | Swap LLM with one --provider flag                       |

---

## Interview Conclusion

This project implements the full perception-action loop of a computer-use agent:
screenshot -> vision LLM -> structured JSON action -> pyautogui execution -> repeat.
The key challenge is grounding: the LLM must map high-level intent to pixel-precise
coordinates on a live desktop. The UI detector (OpenCV + YOLO) injects bounding boxes
into the planner prompt, significantly improving click accuracy. The safety guard and
approval gate prevent unrecoverable actions. The provider abstraction makes the system
model-agnostic -- switching from Claude to local Llama is a single CLI flag. The
cross-session task memory is what separates this from a one-shot script: the agent
remembers what worked and what failed across runs.
