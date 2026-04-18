#!/usr/bin/env python3
"""
Computer-Using Agent — AI that sees your screen and controls your computer.
Usage:
    python main.py                        # interactive goal prompt
    python main.py --goal "open notepad"  # direct goal
    python main.py --auto                 # no confirmation per action (⚠️ careful)
    python main.py --max-steps 20
"""

import argparse
import sys
import time

from screen_capture import capture_screen, image_to_base64
from planner import get_next_action
from executor import execute_action
from memory import Memory


def run_agent(goal: str, auto_approve: bool = False, max_steps: int = 15):
    mem = Memory(session_file=f"session_{int(time.time())}.json")
    mem.goal = goal

    print(f"\n🎯 Goal: {goal}")
    print(f"🔒 Mode: {'AUTO (no confirmation)' if auto_approve else 'SUPERVISED (confirm each step)'}")
    print(f"🔢 Max steps: {max_steps}")
    print("─" * 50)
    print("⚠️  Move mouse to TOP-LEFT corner of screen to emergency stop.")
    print("─" * 50)

    if not auto_approve:
        input("\nPress ENTER when ready to start...")

    time.sleep(2)  # give user time to switch focus to target window

    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}/{max_steps}] Capturing screen...")

        img = capture_screen()
        b64 = image_to_base64(img)

        print("🧠 Thinking...")
        try:
            action = get_next_action(goal, b64, mem.history, step)
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
    parser = argparse.ArgumentParser(description="Computer-Using Agent")
    parser.add_argument("--goal", type=str, help="What should the agent do?")
    parser.add_argument("--auto", action="store_true", help="No confirmation per step (be careful)")
    parser.add_argument("--max-steps", type=int, default=15, help="Maximum actions before stopping")
    args = parser.parse_args()

    goal = args.goal
    if not goal:
        print("\n🤖 Computer-Using Agent")
        print("=" * 40)
        print("Examples:")
        print("  • Open Chrome and search for 'Python tutorials'")
        print("  • Open Notepad and write 'Hello World'")
        print("  • Take a screenshot and save it to Desktop")
        print()
        goal = input("Enter your goal: ").strip()
        if not goal:
            print("No goal provided. Exiting.")
            sys.exit(1)

    run_agent(goal=goal, auto_approve=args.auto, max_steps=args.max_steps)


if __name__ == "__main__":
    main()
