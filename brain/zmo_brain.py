"""Main orchestration loop for ZMO: listen -> think -> speak.

Coordinates:
1. Face state updates (`POST /state` to `face_server.py`)
2. Speech/text input (`voice/stt.py`)
3. LLM routing & emotion extraction (`brain/llm_router.py`)
4. Voice synthesis (`voice/tts.py`)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brain.llm_router import LLMRouter
from config import settings
from voice import stt, tts


def update_face_state(
    state: str,
    emotion: str = "neutral",
    mode: str = "laptop",
) -> bool:
    """Push `{state, emotion, mode}` to `face_server.py` (`POST /state`)."""
    payload = {
        "state": state,
        "emotion": emotion,
        "mode": mode,
    }
    try:
        response = requests.post(
            settings.FACE_STATE_URL,
            json=payload,
            timeout=1.0,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False





def run_single_turn(
    router: LLMRouter,
    use_text_input: bool = False,
    last_emotion: str = "neutral",
) -> tuple[bool, str]:
    """Execute one full listen -> think -> speak -> move cycle.

    Returns `(should_continue, current_emotion)`.
    """
    current_mode = "laptop" if router.current_backend != "ollama" else "offline"
    update_face_state(state="listening", emotion=last_emotion, mode=current_mode)

    user_text = stt.listen(use_text_fallback=use_text_input)
    if not user_text:
        update_face_state(state="idle", emotion=last_emotion, mode=current_mode)
        return True, last_emotion

    cleaned_input = "".join(c for c in user_text.lower() if c.isalnum() or c.isspace()).strip()
    sleep_phrases = (
        "sleep off zmo",
        "sleep off bmo",
        "sleep off",
        "sleep zmo",
        "sleep bmo",
        "go to sleep",
        "bye bmo",
        "bye zmo",
        "goodbye bmo",
        "goodbye zmo",
        "quit",
        "exit",
    )
    if any(phrase in cleaned_input for phrase in sleep_phrases):
        print(f"[zmo] Sleep/exit command recognized: '{user_text.strip()}'")
        update_face_state(state="talking", emotion="sleepy", mode=current_mode)
        tts.speak("Night night friend! ZMO is powering down to sleep. Rise and shine whenever you need me! Beep boop.")
        update_face_state(state="idle", emotion="sleepy", mode=current_mode)
        return False, "sleepy"

    update_face_state(state="thinking", emotion="thinking", mode=current_mode)
    result = router.route_message(user_text)

    if result.announcement:
        update_face_state(
            state="talking",
            emotion="excited" if result.mode == "laptop" else "neutral",
            mode=result.mode,
        )
        tts.speak(result.announcement)

    update_face_state(state="talking", emotion=result.emotion, mode=result.mode)
    tts.speak(result.spoken_text)

    idle_state = "offline" if result.mode == "offline" else "idle"
    update_face_state(state=idle_state, emotion=result.emotion, mode=result.mode)
    return True, result.emotion


WAKE_WORDS = (
    "rise and shine zmo",
    "rise and shine zeemo",
    "rise and shine",
    "wake up zmo",
    "wake up zeemo",
    "wake up",
)


def wait_for_wake_word(
    use_text_input: bool = False,
    mode: str = "laptop",
) -> bool:
    """Listen in low-power standby mode until a wake phrase like 'Rise and shine ZMO' is heard."""
    update_face_state(state="idle", emotion="sleepy", mode=mode)
    print("\n[zmo] ZMO is sleeping in Standby Mode.")
    print("      Say 'Rise and shine ZMO' or 'Wake up ZMO' to wake me up! (or 'quit' to exit)")

    prompt = "Standby (say 'Rise and shine ZMO'): "
    while True:
        try:
            user_text = (
                stt.listen_text_fallback(prompt=prompt)
                if use_text_input
                else stt.listen(timeout=settings.STT_TIMEOUT, use_text_fallback=False)
            )
            if not user_text:
                continue

            cleaned = "".join(c for c in user_text.lower() if c.isalnum() or c.isspace()).strip()

            if cleaned in ("quit", "exit", "shutdown"):
                print("[zmo] Complete shutdown requested.")
                return False

            if any(w in cleaned for w in WAKE_WORDS):
                print(f"[zmo] Wake phrase detected: '{user_text.strip()}' -> Waking up!")
                update_face_state(state="talking", emotion="excited", mode=mode)
                tts.speak("Rise and shine! ZMO is wide awake and ready to play! Beep boop.")
                update_face_state(state="idle", emotion="happy", mode=mode)
                return True
        except (KeyboardInterrupt, SystemExit):
            print("\n[zmo] Standby interrupted.")
            return False
        except Exception as exc:
            print(f"[zmo] Standby listener error: {exc}")


def main() -> int:
    """Entry point for the ZMO brain loop."""
    parser = argparse.ArgumentParser(description="Run the ZMO robot brain loop.")
    parser.add_argument(
        "--text",
        action="store_true",
        help="Force keyboard input() instead of termux-speech-to-text.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single turn and exit (useful for testing).",
    )
    parser.add_argument(
        "--standby",
        action="store_true",
        help="Start directly in sleeping standby mode waiting for 'Rise and shine ZMO'.",
    )
    args = parser.parse_args()

    router = LLMRouter()
    backend, initial_announcement = router.select_backend()
    initial_mode = "laptop" if backend == "lmstudio" else "offline"
    use_text = args.text or settings.USE_TEXT_INPUT

    print(f"[zmo] Starting ZMO brain (active backend: {backend}).")
    update_face_state(state="idle", emotion="happy", mode=initial_mode)

    if initial_announcement and not args.standby:
        update_face_state(state="talking", emotion="happy", mode=initial_mode)
        tts.speak(initial_announcement)
        update_face_state(
            state="offline" if initial_mode == "offline" else "idle",
            emotion="happy",
            mode=initial_mode,
        )

    last_emotion = "happy"
    in_standby = args.standby

    try:
        while True:
            if in_standby:
                woke_up = wait_for_wake_word(use_text_input=use_text, mode=initial_mode)
                if not woke_up:
                    break
                in_standby = False
                last_emotion = "happy"

            keep_going, last_emotion = run_single_turn(
                router=router,
                use_text_input=use_text,
                last_emotion=last_emotion,
            )
            if args.once:
                break
            if not keep_going:
                # User said "Sleep off ZMO" -> transition back to sleeping Standby Mode!
                print("[zmo] Transitioning to Standby Mode...")
                in_standby = True
    except KeyboardInterrupt:
        print("\n[zmo] Shutting down ZMO brain. Beep boop!")
        update_face_state(state="idle", emotion="sleepy", mode=initial_mode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
