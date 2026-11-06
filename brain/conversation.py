"""Conversation history manager with per-backend token budget trimming.

Ensures the system prompt is always preserved and retains the most recent N
user/assistant turns that fit within either the LM Studio budget (~3000 tokens)
or the Ollama TinyLlama budget (~600 tokens).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


def estimate_tokens(text: str) -> int:
    """Estimate token count conservatively (~4 characters per token + role overhead)."""
    if not text:
        return 1
    return max(1, (len(text) + 3) // 4) + 4


@dataclass
class Turn:
    """A single user/assistant dialogue turn."""

    user: str
    assistant: str

    @property
    def tokens(self) -> int:
        """Estimated total tokens consumed by this turn."""
        return estimate_tokens(self.user) + estimate_tokens(self.assistant)


@dataclass
class ConversationHistory:
    """Manages dialogue turns and builds trimmed message lists per backend budget."""

    system_prompt: str = field(default_factory=settings.load_system_prompt)
    turns: list[Turn] = field(default_factory=list)

    def add_turn(self, user_message: str, assistant_message: str) -> None:
        """Record a completed user and assistant exchange."""
        self.turns.append(
            Turn(user=user_message.strip(), assistant=assistant_message.strip())
        )

    def clear(self) -> None:
        """Clear all recorded conversation turns while keeping the system prompt."""
        self.turns.clear()

    def build_messages(
        self,
        user_message: str,
        token_budget: int,
    ) -> list[dict[str, str]]:
        """Build an OpenAI/Ollama-compatible messages list trimmed to `token_budget`.

        Always keeps the system prompt as the first message and `user_message`
        as the final message, inserting as many of the most recent turns as fit.
        """
        sys_msg = {"role": "system", "content": self.system_prompt}
        cur_user_msg = {"role": "user", "content": user_message.strip()}

        used_tokens = estimate_tokens(self.system_prompt) + estimate_tokens(
            user_message
        )
        selected_turns: list[Turn] = []

        for turn in reversed(self.turns):
            turn_cost = turn.tokens
            if used_tokens + turn_cost > token_budget:
                break
            selected_turns.append(turn)
            used_tokens += turn_cost

        selected_turns.reverse()

        messages: list[dict[str, str]] = [sys_msg]
        for turn in selected_turns:
            messages.append({"role": "user", "content": turn.user})
            messages.append({"role": "assistant", "content": turn.assistant})
        messages.append(cur_user_msg)
        return messages

    def build_laptop_messages(self, user_message: str) -> list[dict[str, str]]:
        """Build messages trimmed to the laptop LM Studio history budget (3000 tokens)."""
        return self.build_messages(
            user_message=user_message,
            token_budget=settings.LMSTUDIO_HISTORY_TOKEN_BUDGET,
        )

    def build_ollama_messages(self, user_message: str) -> list[dict[str, str]]:
        """Build messages trimmed to the Termux Ollama history budget (600 tokens)."""
        return self.build_messages(
            user_message=user_message,
            token_budget=settings.OLLAMA_HISTORY_TOKEN_BUDGET,
        )
