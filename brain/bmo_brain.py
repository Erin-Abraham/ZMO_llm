"""Main orchestration loop for BMO: listen -> think -> speak -> move.

Coordinates:
1. Face state updates (`POST /state` to `face_server.py`)
2. Speech/text input (`voice/stt.py`)
3. LLM routing & emotion extraction (`brain/llm_router.py`)
4. ESP32-C3 servo gestures over Wi-Fi HTTP (`POST http://<ESP32_IP>/gesture`)
5. Voice synthesis (`voice/tts.py`)
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


def trigger_servo_gesture(gesture: str) -> bool:
    """Send `POST http://<ESP32_IP>/gesture` with JSON `{"name": gesture}` if ESP32 is enabled."""
    if not settings.ESP32_ENABLED:
        return False
    gesture_name = gesture if gesture in settings.VALID_GESTURES else "rest"
    try:
        response = requests.post(
            settings.ESP32_GESTURE_URL,
            json={"name": gesture_name},
            timeout=settings.ESP32_TIMEOUT,
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
        trigger_servo_gesture("wave")
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
    trigger_servo_gesture(result.gesture)
    tts.speak(result.spoken_text)

    idle_state = "offline" if result.mode == "offline" else "idle"
    update_face_state(state=idle_state, emotion=result.emotion, mode=result.mode)
    return True, result.emotion


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
    args = parser.parse_args()

    router = LLMRouter()
    backend, initial_announcement = router.select_backend()
    initial_mode = "laptop" if backend == "lmstudio" else "offline"

    print(f"[zmo] Starting ZMO brain (active backend: {backend}). Say 'Sleep off ZMO' to stop.")
    update_face_state(state="idle", emotion="happy", mode=initial_mode)
    trigger_servo_gesture("wave")

    if initial_announcement:
        update_face_state(state="talking", emotion="happy", mode=initial_mode)
        tts.speak(initial_announcement)
        update_face_state(
            state="offline" if initial_mode == "offline" else "idle",
            emotion="happy",
            mode=initial_mode,
        )

    last_emotion = "happy"
    try:
        while True:
            keep_going, last_emotion = run_single_turn(
                router=router,
                use_text_input=args.text or settings.USE_TEXT_INPUT,
                last_emotion=last_emotion,
            )
            if not keep_going or args.once:
                break
    except KeyboardInterrupt:
        print("\n[zmo] Shutting down ZMO brain. Beep boop!")
        update_face_state(state="idle", emotion="sleepy", mode=initial_mode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
