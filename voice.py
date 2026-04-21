"""
Phase 13: Voice goal input.
Speak your goal instead of typing it.
Tries Whisper first (offline, better accuracy), falls back to Google STT.
"""
from __future__ import annotations


def listen_for_goal(timeout: int = 10, language: str = "en-US") -> str | None:
    """
    Record audio from the microphone and return the transcribed goal.
    Returns None on failure.
    """
    try:
        return _listen_whisper(timeout)
    except Exception:
        pass
    try:
        return _listen_google(timeout, language)
    except ImportError:
        print("Voice input requires: pip install SpeechRecognition pyaudio")
        return None
    except Exception as e:
        print(f"Voice error: {e}")
        return None


def _listen_google(timeout: int, language: str) -> str:
    import speech_recognition as sr

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("🎤 Calibrating microphone...")
        r.adjust_for_ambient_noise(source, duration=1)
        print(f"🎤 Listening... (speak your goal, up to {timeout}s)")
        audio = r.listen(source, timeout=timeout, phrase_time_limit=30)

    print("🧠 Transcribing (Google STT)...")
    text = r.recognize_google(audio, language=language)
    print(f"✅ Heard: {text}")
    return text


def _listen_whisper(timeout: int) -> str:
    import speech_recognition as sr

    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Calibrating microphone...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("🎤 Listening (Whisper mode)... speak your goal")
        audio = r.listen(source, timeout=timeout, phrase_time_limit=30)

    print("🧠 Transcribing with Whisper...")
    text = r.recognize_whisper(audio, model="base")
    print(f"✅ Heard: {text}")
    return text


def voice_goal_prompt() -> str:
    """
    Interactive prompt: user can speak OR type their goal.
    Press ENTER to activate microphone, or just type directly.
    """
    print("\n🎤 Voice input — press ENTER to speak, or type your goal:")
    user_input = input("> ").strip()

    if user_input:
        return user_input

    goal = listen_for_goal(timeout=15)
    if not goal:
        print("Didn't catch that. Please type your goal:")
        return input("> ").strip()

    confirm = input(f"Heard: \"{goal}\"\nConfirm? [Y/n]: ").strip().lower()
    if confirm == "n":
        return voice_goal_prompt()
    return goal
