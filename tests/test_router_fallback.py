"""Offline unit and integration test for `brain/llm_router.py`.

Simulates the laptop LM Studio server being offline and verifies:
1. Automatic fallback selection of `"ollama"` with the exact announcement:
   `"Running on my own today, I'll do my best!"`
2. No duplicate announcement when the mode stays `"ollama"` on subsequent turns.
3. Automatic upgrade to `"lmstudio"` when the laptop comes online, announcing:
   `"Big brain online!"`
4. Emotion tag stripping (`[happy] ...`) and missing-tag keyword fallback.
5. Per-backend conversation history trimming (3000 vs 600 token budgets).

Must pass with the laptop server switched off. Prints `PASS` or `FAIL`.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brain.conversation import ConversationHistory
from brain.llm_router import LLMRouter, extract_emotion_and_clean_text
from brain.lmstudio_client import LMStudioClient
from brain.ollama_client import OllamaClient
from config import settings


class SimulatedOfflineLMStudio(LMStudioClient):
    """LM Studio stub that points to an unreachable port to simulate laptop offline."""

    def __init__(self) -> None:
        super().__init__(base_url="http://127.0.0.1:9", model="llama-3.1-8b-instruct")
        self.online: bool = False

    def is_healthy(self, timeout: float = 0.2) -> bool:
        if not self.online:
            return super().is_healthy(timeout=0.2)
        return True

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = settings.LMSTUDIO_MAX_TOKENS,
        timeout: float = settings.LMSTUDIO_REQUEST_TIMEOUT,
    ) -> str:
        if not self.online:
            raise RuntimeError("Laptop is offline")
        return "[happy] Beep boop! Big brain BMO is ready to play!"


class SimulatedLocalOllama(OllamaClient):
    """Local Ollama stub for testing fallback behavior when laptop is switched off."""

    def __init__(self) -> None:
        super().__init__(base_url="http://127.0.0.1:11434", model="tinyllama")

    def is_healthy(self, timeout: float = 0.2) -> bool:
        return True

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = settings.OLLAMA_MAX_TOKENS,
        timeout: float = settings.OLLAMA_REQUEST_TIMEOUT,
    ) -> str:
        # Simulate TinyLlama forgetting the bracketed emotion tag
        return "Yay! Let's go on a little adventure together!"


def run_tests() -> bool:
    """Execute all router fallback, tag extraction, and history trimming assertions."""
    print("=== BMO Router Fallback Test (Laptop Offline Simulation) ===")

    lm_stub = SimulatedOfflineLMStudio()
    ollama_stub = SimulatedLocalOllama()
    history = ConversationHistory()
    router = LLMRouter(
        lmstudio_client=lm_stub,
        ollama_client=ollama_stub,
        history=history,
    )

    # 1. Laptop is offline -> must select "ollama" and announce laptop down
    res1 = router.route_message("Hello BMO!")
    assert res1.backend == "ollama", f"Expected 'ollama', got {res1.backend!r}"
    assert res1.mode == "offline", f"Expected mode 'offline', got {res1.mode!r}"
    assert (
        res1.announcement == settings.ANNOUNCEMENT_LAPTOP_DOWN
    ), f"Expected laptop-down announcement, got {res1.announcement!r}"
    # TinyLlama omitted the tag, but used "Yay!" and "!" -> must infer "excited"
    assert res1.emotion == "excited", f"Expected 'excited', got {res1.emotion!r}"
    print("[OK] Step 1: Laptop offline -> selected 'ollama' + announced mode change.")

    # 2. Second message while still offline -> no duplicate mode announcement
    res2 = router.route_message("Are you still there?")
    assert res2.backend == "ollama", f"Expected 'ollama', got {res2.backend!r}"
    assert (
        res2.announcement is None
    ), f"Expected None announcement when mode unchanged, got {res2.announcement!r}"
    print("[OK] Step 2: Subsequent offline turn did not repeat announcement.")

    # 3. Laptop wakes up -> router automatically upgrades to "lmstudio" and announces
    lm_stub.online = True
    res3 = router.route_message("Wake up big brain!")
    assert res3.backend == "lmstudio", f"Expected 'lmstudio', got {res3.backend!r}"
    assert res3.mode == "laptop", f"Expected mode 'laptop', got {res3.mode!r}"
    assert (
        res3.announcement == settings.ANNOUNCEMENT_LAPTOP_UP
    ), f"Expected laptop-up announcement, got {res3.announcement!r}"
    assert res3.emotion == "happy", f"Expected 'happy', got {res3.emotion!r}"
    assert not res3.spoken_text.startswith(
        "[happy]"
    ), f"Tag was not stripped from spoken_text: {res3.spoken_text!r}"
    print("[OK] Step 3: Laptop wake-up -> upgraded to 'lmstudio' + stripped [happy] tag.")

    # 4. Verify keyword fallback rules from Section 4
    emo_exc, txt_exc = extract_emotion_and_clean_text("Yay we won")
    assert emo_exc == "excited" and txt_exc == "Yay we won"

    emo_sad, _ = extract_emotion_and_clean_text("I am so sorry Finn.")
    assert emo_sad == "sad"

    emo_thk, _ = extract_emotion_and_clean_text("Where did Jake hide the batteries?")
    assert emo_thk == "thinking"

    emo_neu, _ = extract_emotion_and_clean_text("BMO is a real living boy.")
    assert emo_neu == "neutral"
    print("[OK] Step 4: Emotion tag parser and keyword fallback verified.")

    # 5. Verify history budget trimming preserves system prompt and respects 600 vs 3000 tokens
    for i in range(30):
        history.add_turn(
            f"User question number {i} with extra padding words to consume token budget.",
            f"[happy] BMO answer number {i} with extra cheerful words and beep boop!",
        )
    ollama_msgs = history.build_ollama_messages("Final question?")
    laptop_msgs = history.build_laptop_messages("Final question?")
    assert ollama_msgs[0]["role"] == "system", "System prompt missing from Ollama messages!"
    assert laptop_msgs[0]["role"] == "system", "System prompt missing from Laptop messages!"
    assert len(ollama_msgs) < len(
        laptop_msgs
    ), "Ollama 600-token history should retain fewer turns than Laptop 3000-token history."
    print(
        f"[OK] Step 5: History budget trimming verified "
        f"(Ollama messages={len(ollama_msgs)}, Laptop messages={len(laptop_msgs)})."
    )

    return True


def main() -> int:
    try:
        ok = run_tests()
    except AssertionError as err:
        print(f"\nFAIL: {err}")
        return 1
    except Exception as exc:
        print(f"\nFAIL: Unexpected error: {exc}")
        return 1

    if ok:
        print("\nPASS")
        return 0
    print("\nFAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
