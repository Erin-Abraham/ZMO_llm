"""Speech-to-text (STT) input wrapper for ZMO.

Uses `termux-speech-to-text` on the Samsung Galaxy A07 with a configurable
timeout, and automatically falls back to terminal `input()` when running on
the Windows laptop or when `USE_TEXT_INPUT=true`.
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


def is_termux_stt_available() -> bool:
    """Return True if `termux-speech-to-text` is on PATH and text fallback is not forced."""
    if settings.USE_TEXT_INPUT:
        return False
    return shutil.which("termux-speech-to-text") is not None


def listen_termux(timeout: float = settings.STT_TIMEOUT) -> str:
    """Capture a single utterance via `termux-speech-to-text` with a timeout."""
    try:
        completed = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode == 0:
            return completed.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except OSError as exc:
        print(f"[stt] termux-speech-to-text failed: {exc}")
    return ""


def listen_text_fallback(prompt: str = "You: ") -> str:
    """Read a line of user input from stdin (`input()`) for laptop/mic-free testing."""
    try:
        return input(prompt).strip()
    except EOFError:
        return "quit"


def listen(
    timeout: float = settings.STT_TIMEOUT,
    use_text_fallback: bool | None = None,
) -> str:
    """Listen for user speech via Termux:API or fall back to keyboard `input()`."""
    force_text = (
        settings.USE_TEXT_INPUT if use_text_fallback is None else use_text_fallback
    )
    if not force_text and is_termux_stt_available():
        print("[stt] Listening via termux-speech-to-text...")
        heard = listen_termux(timeout=timeout)
        if heard:
            print(f"You (voice): {heard}")
        return heard
    return listen_text_fallback()
