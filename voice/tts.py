"""Text-to-speech (TTS) output wrapper for BMO.

Uses `termux-tts-speak` on the Samsung Galaxy A07 and `pyttsx3` on the Windows
laptop for local testing. Exposes `pitch` and `rate` parameters so the user can
tune a higher, childlike BMO voice, and wraps execution in a timeout.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


def is_termux_tts_available() -> bool:
    """Return True if `termux-tts-speak` is available on PATH."""
    return shutil.which("termux-tts-speak") is not None


def _speak_termux(
    text: str,
    pitch: float,
    rate: float,
    timeout: float,
) -> bool:
    """Speak `text` using `termux-tts-speak -p <pitch> -r <rate>` with a timeout."""
    try:
        completed = subprocess.run(
            [
                "termux-tts-speak",
                "-p",
                f"{pitch:.2f}",
                "-r",
                f"{rate:.2f}",
                text,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[tts] termux-tts-speak timed out after {timeout:.1f}s.")
        return False
    except OSError as exc:
        print(f"[tts] termux-tts-speak error: {exc}")
        return False


def _speak_laptop_pyttsx3(
    text: str,
    pitch: float,
    rate: float,
    timeout: float,
) -> bool:
    """Speak `text` on Windows laptop using `pyttsx3` inside a timed child process."""
    # Running pyttsx3 in a short child process ensures clean COM teardown and strict timeout.
    wpm = int(175 * max(0.5, min(rate, 2.0)))
    code = (
        "import sys, pyttsx3; "
        "engine = pyttsx3.init(); "
        f"engine.setProperty('rate', {wpm}); "
        "engine.say(sys.argv[1]); "
        "engine.runAndWait()"
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-c", code, text],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[tts] pyttsx3 timed out after {timeout:.1f}s.")
        return False
    except OSError:
        return False


def speak(
    text: str,
    pitch: float = settings.TTS_PITCH,
    rate: float = settings.TTS_RATE,
    timeout: float = settings.TTS_TIMEOUT,
) -> bool:
    """Speak `text` with BMO's voice settings and return True if audio played."""
    cleaned = text.strip()
    if not cleaned:
        return False

    print(f"BMO: {cleaned}")

    if is_termux_tts_available():
        return _speak_termux(cleaned, pitch=pitch, rate=rate, timeout=timeout)

    if sys.platform == "win32":
        return _speak_laptop_pyttsx3(cleaned, pitch=pitch, rate=rate, timeout=timeout)

    return False
