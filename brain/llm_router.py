"""LLM router with per-message health check, automatic fallback, and emotion parsing.

Responsibilities (per Section 4 and Section 5.1 of `skills.md`):
- Before every user message, health-check the laptop LM Studio server with a 2 s timeout.
- If LM Studio answers, use it (`lmstudio`); otherwise fall back to Ollama (`ollama`).
- Re-check on every message so BMO automatically upgrades when the laptop wakes up.
- Emit a mode-change announcement ONLY when the active backend changes:
  * Laptop up: "Big brain online!"
  * Laptop down: "Running on my own today, I'll do my best!"
- Strip the leading `[emotion]` tag from the reply before speaking and map it to
  both face emotion and ESP32 servo gesture.
- If the tag is missing (common with TinyLlama), infer emotion from keywords:
  * `!` or `yay` -> `excited`
  * `sorry` -> `sad`
  * `?` -> `thinking`
  * otherwise -> `neutral`
- On request timeout or error, fall back once to the secondary backend, then
  return a friendly in-character line without ever crashing.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brain.conversation import ConversationHistory
from brain.lmstudio_client import LMStudioClient
from brain.ollama_client import OllamaClient
from config import settings

_LEADING_TAG_RE = re.compile(r"^\s*\[([a-zA-Z_ -]+)\]\s*(.*)$", re.DOTALL)


@dataclass
class RouteResult:
    """Structured result returned by `LLMRouter.route_message`."""

    spoken_text: str
    raw_reply: str
    emotion: str
    backend: str
    mode: str
    announcement: str | None = None


def infer_emotion_from_keywords(text: str) -> str:
    """Fallback emotion classifier when the model omits a bracketed emotion tag."""
    lowered = text.lower()
    if "!" in text or "yay" in lowered:
        return "excited"
    if "sorry" in lowered:
        return "sad"
    if "?" in text:
        return "thinking"
    return "neutral"


def extract_emotion_and_clean_text(raw_reply: str) -> tuple[str, str]:
    """Strip the leading `[emotion]` tag from `raw_reply` and return `(emotion, clean_text)`.

    Falls back to keyword matching if the tag is missing or unrecognized.
    """
    cleaned = raw_reply.strip()
    match = _LEADING_TAG_RE.match(cleaned)
    if match:
        candidate_tag = match.group(1).strip().lower()
        remainder = match.group(2).strip()
        # Strip any additional consecutive bracket tags if the LLM emitted more than one
        while True:
            next_match = _LEADING_TAG_RE.match(remainder)
            if not next_match:
                break
            remainder = next_match.group(2).strip()

        if candidate_tag in settings.VALID_EMOTIONS:
            spoken = remainder if remainder else "Beep boop!"
            return candidate_tag, spoken
        # Tag was present but not in VALID_EMOTIONS: still strip the bracket tag and infer
        spoken = remainder if remainder else cleaned
        return infer_emotion_from_keywords(spoken), spoken

    return infer_emotion_from_keywords(cleaned), (cleaned or "Beep boop!")


class LLMRouter:
    """Routes user messages between LM Studio (laptop) and Ollama (Termux fallback)."""

    def __init__(
        self,
        lmstudio_client: LMStudioClient | None = None,
        ollama_client: OllamaClient | None = None,
        history: ConversationHistory | None = None,
    ) -> None:
        self.lmstudio: LMStudioClient = lmstudio_client or LMStudioClient()
        self.ollama: OllamaClient = ollama_client or OllamaClient()
        self.history: ConversationHistory = history or ConversationHistory()
        self.current_backend: str | None = None

    def select_backend(self) -> tuple[str, str | None]:
        """Health-check laptop with a 2 s timeout and return `(backend, announcement)`.

        `backend` is either `"lmstudio"` or `"ollama"`.
        `announcement` is non-None only when the mode changes.
        """
        laptop_up = self.lmstudio.is_healthy(timeout=settings.HEALTH_CHECK_TIMEOUT)
        new_backend = "lmstudio" if laptop_up else "ollama"

        announcement: str | None = None
        if new_backend != self.current_backend:
            if new_backend == "lmstudio":
                announcement = settings.ANNOUNCEMENT_LAPTOP_UP
            else:
                announcement = settings.ANNOUNCEMENT_LAPTOP_DOWN
            self.current_backend = new_backend

        return new_backend, announcement

    def _call_backend(self, backend: str, user_message: str) -> str:
        """Build budget-trimmed messages and query the specified backend."""
        if backend == "lmstudio":
            messages = self.history.build_laptop_messages(user_message)
            return self.lmstudio.chat(
                messages=messages,
                max_tokens=settings.LMSTUDIO_MAX_TOKENS,
                timeout=settings.LMSTUDIO_REQUEST_TIMEOUT,
            )
        messages = self.history.build_ollama_messages(user_message)
        return self.ollama.chat(
            messages=messages,
            max_tokens=settings.OLLAMA_MAX_TOKENS,
            timeout=settings.OLLAMA_REQUEST_TIMEOUT,
        )

    def route_message(self, user_message: str) -> RouteResult:
        """Route a user message, handling fallback on timeout/error and tag stripping."""
        backend, announcement = self.select_backend()
        raw_reply: str | None = None

        try:
            raw_reply = self._call_backend(backend, user_message)
        except (requests.RequestException, RuntimeError, ValueError) as primary_err:
            print(f"[router] Primary backend '{backend}' failed ({primary_err}); attempting fallback once.")
            if backend == "lmstudio":
                backend = "ollama"
                if self.current_backend != "ollama":
                    self.current_backend = "ollama"
                    announcement = settings.ANNOUNCEMENT_LAPTOP_DOWN
                try:
                    raw_reply = self._call_backend("ollama", user_message)
                except (requests.RequestException, RuntimeError, ValueError) as fallback_err:
                    print(f"[router] Fallback backend 'ollama' also failed: {fallback_err}")
            else:
                # Primary was already ollama; try laptop once in case it just came up
                try:
                    if self.lmstudio.is_healthy(timeout=settings.HEALTH_CHECK_TIMEOUT):
                        backend = "lmstudio"
                        self.current_backend = "lmstudio"
                        announcement = settings.ANNOUNCEMENT_LAPTOP_UP
                        raw_reply = self._call_backend("lmstudio", user_message)
                except (requests.RequestException, RuntimeError, ValueError) as fallback_err:
                    print(f"[router] Fallback check failed: {fallback_err}")

        if not raw_reply:
            spoken = settings.FRIENDLY_ERROR_REPLY
            emotion = "sad"
            mode = "laptop" if self.current_backend == "lmstudio" else "offline"
            return RouteResult(
                spoken_text=spoken,
                raw_reply=f"[sad] {spoken}",
                emotion=emotion,
                backend=self.current_backend or "ollama",
                mode=mode,
                announcement=announcement,
            )

        emotion, spoken_text = extract_emotion_and_clean_text(raw_reply)
        self.history.add_turn(user_message=user_message, assistant_message=raw_reply)
        mode = "laptop" if backend == "lmstudio" else "offline"

        return RouteResult(
            spoken_text=spoken_text,
            raw_reply=raw_reply,
            emotion=emotion,
            backend=backend,
            mode=mode,
            announcement=announcement,
        )
