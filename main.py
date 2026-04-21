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
    python main.py --goal "..." --dashboard             # Phase 12: live web dashboard
    python main.py --voice                              # Phase 13: speak your goal
    python main.py --goal "..." --detect                # Phase 10: UI element detection
    python main.py --goal "..." --rollback              # Phase 14: auto-rollback on failure
"""

import argparse
import sys
import time

from screen_capture import capture_screen, image_to_base64
from planner import get_next_action
from executor import execute_action
from memory import Memory
from providers import PROVIDERS, list_providers
from logger import Logger


def run_agent(
    goal: str,
    provider: str = "anthropic",
    model: str | None = None,
    auto_approve: bool = False,
    max_steps: int = 15,
    use_dashboard: bool = False,
    use_detect: bool = False,
    use_rollback: bool = False,
):
    info = PROVIDERS[provider]
    effective_model = model or info["default_model"]
    session_id = str(int(time.time()))

    # Phase 12: start web dashboard
    _dash_emit = None
    if use_dashboard:
        try:
            from dashboard import start_dashboard, emit_event, emit_screenshot
            start_dashboard()
            _dash_emit = emit_event
            _dash_screenshot = emit_screenshot
            _dash_emit("session_start", {
                "goal": goal, "provider": provider,
                "model": effective_model, "session_id": session_id,
            })
        except ImportError as e:
            print(f"⚠️  Dashboard unavailable: {e}")
            use_dashboard = False
            _dash_screenshot = lambda _: None
    else:
        _dash_screenshot = lambda _: None

    mem = Memory(session_file=f"session_{session_id}.json")
    mem.goal = goal
    log = Logger(session_id=session_id, goal=goal, provider=provider, model=effective_model)

    # Phase 14: rollback manager
    rollback_mgr = None
    if use_rollback:
        from rollback import RollbackManager
        rollback_mgr = RollbackManager(session_id)

    print(f"\n🎯 Goal: {goal}")
    print(f"🤖 Provider: {info['name']}  |  Model: {effective_model}")
    if not info["vision"]:
        print(f"⚠️  Note: {info.get('note', 'No vision — using text-only mode')}")
    print(f"🔒 Mode: {'AUTO (no confirmation)' if auto_approve else 'SUPERVISED (confirm each step)'}")
    print(f"🔢 Max steps: {max_steps}")
    if use_detect:
        print("🔍 UI detection: ON")
    if use_rollback:
        print("🔄 Rollback: ON")
    if use_dashboard:
        print("📊 Dashboard: ON")
    print("─" * 55)
    print("⚠️  Move mouse to TOP-LEFT corner to emergency stop.")
    print("─" * 55)

    # Phase 11: fetch cross-session context once at start
    task_ctx = mem.get_task_context()
    if task_ctx:
        print(f"\n📚 Cross-session context loaded:\n{task_ctx}\n")

    if not auto_approve:
        input("\nPress ENTER when ready to start...")

    time.sleep(2)

    status = "completed"
    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}/{max_steps}] Capturing screen...")

        img = capture_screen()
        b64 = image_to_base64(img)
        log.screen_capture(step, img.size)
        _dash_screenshot(img)

        # Phase 10: UI element detection
        detected = None
        if use_detect:
            try:
                from detector import detect_ui_elements
                detected = detect_ui_elements(img)
                if detected:
                    print(f"🔍 Detected {len(detected)} UI elements")
            except Exception as e:
                print(f"⚠️  Detection skipped: {e}")

        print("🧠 Thinking...")
        try:
            action = get_next_action(
                goal=goal,
                screenshot_b64=b64,
                history=mem.history,
                step=step,
                provider=provider,
                model=model,
                logger=log,
                detected_elements=detected,
                task_memory_context=task_ctx,
            )
        except Exception as e:
            print(f"❌ Planner error: {e}")
            log.error(str(e))
            if _dash_emit:
                _dash_emit("error", {"message": str(e)})
            # Phase 14: rollback on planner error
            if rollback_mgr:
                rollback_mgr.rollback("planner error", dashboard_emit=_dash_emit)
            status = "error"
            break

        print(f"💡 Decided: {action.get('type')} — {action.get('reasoning', '')}")
        log.step(step, action)

        if _dash_emit:
            _dash_emit("step", {
                "step": step, "max_steps": max_steps,
                "type": action.get("type"),
                "reasoning": action.get("reasoning", ""),
            })

        if action.get("type") == "done":
            print("\n✅ Agent says goal is complete!")
            break

        # Phase 14: checkpoint before risky action
        if rollback_mgr and rollback_mgr.should_checkpoint(action):
            rollback_mgr.checkpoint(step, action, img)

        should_continue = execute_action(action, auto_approve=auto_approve, logger=log)
        mem.add(action)

        if not should_continue:
            if _dash_emit:
                _dash_emit("blocked", {"reason": "user stopped or action blocked"})
            status = "stopped"
            break

    if _dash_emit:
        _dash_emit("done", {"steps": len(mem.history), "status": status})

    log.session_end(steps=len(mem.history), status=status)
    mem.save(status=status, provider=provider)
    print(f"\n📊 Summary:\n{mem.summary()}")

    if rollback_mgr:
        rb_summary = rollback_mgr.summary()
        if rb_summary != "No rollbacks triggered.":
            print(f"\n🔄 Rollback log:\n{rb_summary}")


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
  python main.py --voice                        # speak your goal
  python main.py --goal "..." --dashboard       # live web dashboard
  python main.py --goal "..." --detect          # UI element detection
  python main.py --goal "..." --rollback        # auto-rollback on failure
        """,
    )
    parser.add_argument("--goal", type=str, help="What should the agent do?")
    parser.add_argument(
        "--provider", type=str, default="anthropic",
        choices=list(PROVIDERS.keys()),
        help="LLM provider to use (default: anthropic)",
    )
    parser.add_argument("--model", type=str, default=None,
                        help="Override default model for the provider")
    parser.add_argument("--auto", action="store_true",
                        help="No confirmation per step (be careful)")
    parser.add_argument("--max-steps", type=int, default=15,
                        help="Max actions before stopping")
    parser.add_argument("--list-providers", action="store_true",
                        help="Show all supported providers and exit")
    # Phase 10
    parser.add_argument("--detect", action="store_true",
                        help="Enable YOLO/OpenCV UI element detection for better click accuracy")
    # Phase 12
    parser.add_argument("--dashboard", action="store_true",
                        help="Open live web dashboard at http://127.0.0.1:7860")
    # Phase 13
    parser.add_argument("--voice", action="store_true",
                        help="Speak your goal instead of typing it")
    # Phase 14
    parser.add_argument("--rollback", action="store_true",
                        help="Auto-rollback on action failure (Ctrl+Z + clipboard restore)")

    args = parser.parse_args()

    if args.list_providers:
        list_providers()
        sys.exit(0)

    goal = args.goal

    # Phase 13: voice input
    if args.voice and not goal:
        from voice import voice_goal_prompt
        goal = voice_goal_prompt()
    elif not goal:
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
        print(f"Unknown provider '{args.provider}'. Run --list-providers to see options.")
        sys.exit(1)

    run_agent(
        goal=goal,
        provider=args.provider,
        model=args.model,
        auto_approve=args.auto,
        max_steps=args.max_steps,
        use_dashboard=args.dashboard,
        use_detect=args.detect,
        use_rollback=args.rollback,
    )


if __name__ == "__main__":
    main()
