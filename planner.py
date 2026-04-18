import json
import re

from providers import call_provider
from logger import Logger

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


def get_next_action(
    goal: str,
    screenshot_b64: str,
    history: list[dict],
    step: int,
    provider: str = "anthropic",
    model: str | None = None,
    logger: Logger | None = None,
) -> dict:
    history_text = ""
    if history:
        last = history[-5:]
        history_text = "\n\nPrevious actions taken:\n" + "\n".join(
            f"  Step {i+1}: {json.dumps(a)}" for i, a in enumerate(last)
        )

    prompt = f"Step {step}. Goal: {goal}{history_text}\n\nWhat is the single next action to take? Respond with JSON only."

    effective_model = model or ""
    if logger:
        logger.llm_call(provider, effective_model)

    raw = call_provider(
        provider=provider,
        system=SYSTEM_PROMPT,
        prompt=prompt,
        image_b64=screenshot_b64,
        model=model,
    )

    if logger:
        logger.llm_response(raw)

    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())

    raise ValueError(f"Could not parse action from response: {raw}")
