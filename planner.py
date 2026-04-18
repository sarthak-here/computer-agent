import anthropic
import json
import re

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an AI agent controlling a Windows computer. You see the screen and decide the next single action to take toward the user's goal.

You must respond with ONLY a valid JSON object — no markdown, no explanation outside JSON.

Action types:
- click: {"type": "click", "x": int, "y": int, "button": "left"|"right", "double": bool, "reasoning": "..."}
- type: {"type": "type", "text": "...", "reasoning": "..."}
- press: {"type": "press", "key": "enter"|"tab"|"escape"|"backspace"|..., "reasoning": "..."}
- hotkey: {"type": "hotkey", "keys": ["ctrl", "c"], "reasoning": "..."}
- scroll: {"type": "scroll", "x": int, "y": int, "clicks": int, "reasoning": "..."}
- wait: {"type": "wait", "seconds": float, "reasoning": "..."}
- done: {"type": "done", "reasoning": "Goal is complete"}

Rules:
- Take ONE action at a time
- If the goal is already complete, return done
- x and y are pixel coordinates on screen
- Be precise with coordinates — look carefully at the screenshot
- If unsure, use a conservative action or wait"""


def get_next_action(goal: str, screenshot_b64: str, history: list[dict], step: int) -> dict:
    history_text = ""
    if history:
        last = history[-5:]  # only last 5 actions for context
        history_text = "\n\nPrevious actions taken:\n" + "\n".join(
            f"  Step {i+1}: {json.dumps(a)}" for i, a in enumerate(last)
        )

    user_content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
        },
        {
            "type": "text",
            "text": f"Step {step}. Goal: {goal}{history_text}\n\nWhat is the single next action to take? Respond with JSON only.",
        },
    ]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()

    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())

    raise ValueError(f"Could not parse action from response: {raw}")
