#!/usr/bin/env python3
"""
Computer-Using Agent — AI that sees your screen and controls your computer.

Usage:
    python main.py                                        # interactive
    python main.py --goal "open notepad"
    python main.py --goal "..." --provider openai
    python main.py --goal "..." --provider ollama --model llava
    python main.py --goal "..." --provider gemini --model gemini-1.5-flash
    python main.py --list-providers
    python main.py --auto --max-steps 20
"""

import argparse
import sys
import time

from screen_capture import capture_screen, image_to_base64
from planner import get_next_action
from executor import execute_action
from memory import Memory
from providers import PROVIDERS, list_providers


def run_agent(
    goal: str,
    provider: str = "anthropic",
    model: str | None = None,
    auto_approve: bool = False,
    max_steps: int = 15,
):
    info = PROVIDERS[provider]
    effective_model = model or info["default_model"]

    mem = Memory(session_file=f"session_{int(time.time())}.json")
    mem.goal = goal

    print(f"\n🎯 Goal: {goal}")
    print(f"🤖 Provider: {info['name']}  |  Model: {effective_model}")
    if not info["vision"]:
        print(f"⚠️  Note: {info.get('note', 'No vision — using text-only mode')}")
    print(f"🔒 Mode: {'AUTO (no confirmation)' if auto_approve else 'SUPERVISED (confirm each step)'}")
    print(f"🔢 Max steps: {max_steps}")
    print("─" * 55)
    print("⚠️  Move mouse to TOP-LEFT corner of screen to emergency stop.")
    print("─" * 55)

    if not auto_approve:
        input("\nPress ENTER when ready to start...")

    time.sleep(2)

    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}/{max_steps}] Capturing screen...")

        img = capture_screen()
        b64 = image_to_base64(img)

        print("🧠 Thinking...")
        try:
            action = get_next_action(
                goal=goal,
                screenshot_b64=b64,
                history=mem.history,
                step=step,
                provider=provider,
                model=model,
            )
        except Exception as e:
            print(f"❌ Planner error: {e}")
            break

        print(f"💡 Decided: {action.get('type')} — {action.get('reasoning', '')}")

        if action.get("type") == "done":
            print("\n✅ Agent says goal is complete!")
            break

        should_continue = execute_action(action, auto_approve=auto_approve)
        mem.add(action)

        if not should_continue:
            break

    mem.save()
    print(f"\n📊 Summary:\n{mem.summary()}")


def main():
    parser = argparse.ArgumentParser(
        description="Computer-Using Agent — AI controls your screen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --goal "open notepad"
  python main.py --goal "search Python tutorials" --provider openai
  python main.py --goal "..." --provider ollama --model llava
  python main.py --goal "..." --provider gemini --model gemini-1.5-flash
  python main.py --goal "..." --provider groq
  python main.py --list-providers
        """,
    )
    parser.add_argument("--goal", type=str, help="What should the agent do?")
    parser.add_argument(
        "--provider", type=str, default="anthropic",
        choices=list(PROVIDERS.keys()),
        help="LLM provider to use (default: anthropic)",
    )
    parser.add_argument("--model", type=str, default=None, help="Override default model for the provider")
    parser.add_argument("--auto", action="store_true", help="No confirmation per step (be careful)")
    parser.add_argument("--max-steps", type=int, default=15, help="Max actions before stopping")
    parser.add_argument("--list-providers", action="store_true", help="Show all supported providers and exit")
    args = parser.parse_args()

    if args.list_providers:
        list_providers()
        sys.exit(0)

    goal = args.goal
    if not goal:
        print("\n🤖 Computer-Using Agent")
        print("=" * 45)
        list_providers()
        print()
        print("Examples:")
        print("  • Open Chrome and search for 'Python tutorials'")
        print("  • Open Notepad and write 'Hello World'")
        print("  • Open calculator and compute 1234 × 5678")
        print()
        goal = input("Enter your goal: ").strip()
        if not goal:
            print("No goal provided. Exiting.")
            sys.exit(1)

    if args.provider not in PROVIDERS:
        print(f"Unknown provider '{args.provider}'. Run with --list-providers to see options.")
        sys.exit(1)

    run_agent(
        goal=goal,
        provider=args.provider,
        model=args.model,
        auto_approve=args.auto,
        max_steps=args.max_steps,
    )


if __name__ == "__main__":
    main()
