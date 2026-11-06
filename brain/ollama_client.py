"""Ollama API client for the Termux fallback LLM (`tinyllama` on port 11434).

Uses `GET /api/tags` for health checking and `POST /api/chat` with `stream: false`,
`num_ctx: 1024`, and `max_tokens: 80` (`num_predict`).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


class OllamaClient:
    """Client for Ollama running locally in Termux on port 11434."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url: str = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.tags_url: str = f"{self.base_url}/api/tags"
        self.chat_url: str = f"{self.base_url}/api/chat"
        self.model: str = (model or settings.OLLAMA_MODEL).strip() or "tinyllama"

    def list_models(
        self, timeout: float = settings.HEALTH_CHECK_TIMEOUT
    ) -> list[str]:
        """Fetch installed Ollama model names from `GET /api/tags`."""
        response = requests.get(self.tags_url, timeout=timeout)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        models = payload.get("models", [])
        names: list[str] = []
        if isinstance(models, list):
            for item in models:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item["name"]))
        return names

    def is_healthy(
        self, timeout: float = settings.HEALTH_CHECK_TIMEOUT
    ) -> bool:
        """Check if Ollama responds on `GET /api/tags` within `timeout` seconds."""
        try:
            self.list_models(timeout=timeout)
            return True
        except requests.RequestException:
            return False
        except ValueError:
            return False

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = settings.OLLAMA_MAX_TOKENS,
        timeout: float = settings.OLLAMA_REQUEST_TIMEOUT,
    ) -> str:
        """Send a non-streaming chat request to `POST /api/chat`."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": settings.OLLAMA_NUM_CTX,
                "num_predict": max_tokens,
                "temperature": settings.OLLAMA_TEMPERATURE,
                "top_p": settings.OLLAMA_TOP_P,
                "top_k": settings.OLLAMA_TOP_K,
                "repeat_penalty": settings.OLLAMA_REPEAT_PENALTY,
            },
        }
        response = requests.post(self.chat_url, json=payload, timeout=timeout)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        message = data.get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama returned an empty message content.")
        return content.strip()
