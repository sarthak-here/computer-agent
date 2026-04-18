import pyautogui
import time

pyautogui.FAILSAFE = True  # move mouse to top-left corner to abort
pyautogui.PAUSE = 0.3


def click(x: int, y: int, button: str = "left", double: bool = False):
    pyautogui.moveTo(x, y, duration=0.3)
    if double:
        pyautogui.doubleClick(x, y)
    else:
        pyautogui.click(x, y, button=button)


def type_text(text: str, interval: float = 0.05):
    pyautogui.typewrite(text, interval=interval)


def press_key(key: str):
    pyautogui.press(key)


def hotkey(*keys: str):
    pyautogui.hotkey(*keys)


def scroll(x: int, y: int, clicks: int):
    pyautogui.scroll(clicks, x=x, y=y)


def move_to(x: int, y: int):
    pyautogui.moveTo(x, y, duration=0.3)


SAFE_GUARD_KEYWORDS = ["delete", "format", "rm -rf", "drop table", "shutdown", "uninstall"]


def is_dangerous(action_desc: str) -> bool:
    return any(kw in action_desc.lower() for kw in SAFE_GUARD_KEYWORDS)


def execute_action(action: dict, auto_approve: bool = False, logger=None) -> bool:
    atype = action.get("type", "")
    desc = action.get("reasoning", "")

    if is_dangerous(desc) or is_dangerous(str(action)):
        print(f"\n⚠️  DANGEROUS ACTION DETECTED: {action}")
        confirm = input("Allow? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Action blocked.")
            if logger:
                logger.blocked(action, "dangerous action denied by user")
            return False

    if not auto_approve:
        print(f"\n🤖 Proposed action: {action}")
        confirm = input("Execute? [Y/n/s(skip)]: ").strip().lower()
        if confirm == "n":
            if logger:
                logger.blocked(action, "user denied")
            return False
        if confirm == "s":
            if logger:
                logger.blocked(action, "user skipped")
            return True

    if atype == "click":
        click(action["x"], action["y"], action.get("button", "left"), action.get("double", False))
    elif atype == "type":
        type_text(action["text"])
    elif atype == "press":
        press_key(action["key"])
    elif atype == "hotkey":
        hotkey(*action["keys"])
    elif atype == "scroll":
        scroll(action["x"], action["y"], action["clicks"])
    elif atype == "wait":
        time.sleep(action.get("seconds", 1))
    elif atype == "done":
        print("\n✅ Goal completed!")
        return False
    else:
        print(f"Unknown action type: {atype}")

    time.sleep(0.5)
    return True
