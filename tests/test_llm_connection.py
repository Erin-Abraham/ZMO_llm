"""Connectivity test for LM Studio (laptop) and Ollama (Termux fallback).

Pings `GET /v1/models` on LM Studio and `GET /api/tags` on Ollama, reports
which backend(s) are live, sends a quick test prompt if a server is reachable,
and prints `PASS` or `FAIL`.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brain.llm_router import extract_emotion_and_clean_text
from brain.lmstudio_client import LMStudioClient
from brain.ollama_client import OllamaClient
from config import settings


def main() -> int:
    """Ping LM Studio and Ollama, print status, and output PASS or FAIL."""
    lmstudio = LMStudioClient()
    ollama = OllamaClient()

    print("=== ZMO LLM Connection Check ===")
    print(f"1. Checking LM Studio at {lmstudio.models_url} ...")
    lmstudio_up = lmstudio.is_healthy(timeout=settings.HEALTH_CHECK_TIMEOUT)
    if lmstudio_up:
        models = lmstudio.list_models(timeout=settings.HEALTH_CHECK_TIMEOUT)
        print(f"   [LIVE] LM Studio responded. Loaded models: {models or ['(none listed)']}")
    else:
        print("   [OFFLINE] LM Studio did not respond within 2.0 s.")

    print(f"2. Checking Ollama at {ollama.tags_url} ...")
    ollama_up = ollama.is_healthy(timeout=settings.HEALTH_CHECK_TIMEOUT)
    if ollama_up:
        models = ollama.list_models(timeout=settings.HEALTH_CHECK_TIMEOUT)
        print(f"   [LIVE] Ollama responded. Installed models: {models or ['(none listed)']}")
    else:
        print("   [OFFLINE] Ollama did not respond within 2.0 s.")

    if not lmstudio_up and not ollama_up:
        print(
            "\nFAIL: Neither LM Studio (port 1234) nor Ollama (port 11434) is reachable."
        )
        print(
            "      Start LM Studio's Local Server on port 1234 (with Llama 3.1 8B Instruct Q4_K_M)"
        )
        print("      or start `ollama serve` on port 11434, then re-run this test.")
        return 1

    # Send a quick smoke-test completion to whichever backend is live
    messages = [
        {"role": "system", "content": settings.load_system_prompt()},
        {"role": "user", "content": "Say hello in one short sentence!"},
    ]

    try:
        if lmstudio_up:
            raw = lmstudio.chat(messages=messages, max_tokens=60)
            emotion, clean = extract_emotion_and_clean_text(raw)
            print(f"\n[LM Studio Reply] emotion={emotion} | text={clean!r}")
        else:
            raw = ollama.chat(messages=messages, max_tokens=60)
            emotion, clean = extract_emotion_and_clean_text(raw)
            print(f"\n[Ollama Reply] emotion={emotion} | text={clean!r}")
    except Exception as exc:
        print(f"\nFAIL: Server responded to health check, but chat completion failed: {exc}")
        return 1

    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
