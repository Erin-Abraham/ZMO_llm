"""OpenAI-compatible client for LM Studio running on the Windows laptop.

Uses `GET /v1/models` for the 2-second health check and model auto-discovery,
and `POST /v1/chat/completions` for chat generation. Never uses `/api/chat`.
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


class LMStudioClient:
    """Client for LM Studio's OpenAI-compatible HTTP server on port 1234."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url: str = (base_url or settings.LMSTUDIO_BASE_URL).rstrip("/")
        self.models_url: str = f"{self.base_url}/v1/models"
        self.chat_url: str = f"{self.base_url}/v1/chat/completions"
        self.configured_model: str = (
            model if model is not None else settings.LMSTUDIO_MODEL
        ).strip()
        self._discovered_model: str | None = None

    def list_models(
        self, timeout: float = settings.HEALTH_CHECK_TIMEOUT
    ) -> list[str]:
        """Fetch available model IDs from `GET /v1/models`."""
        response = requests.get(self.models_url, timeout=timeout)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        data = payload.get("data", [])
        model_ids: list[str] = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("id"):
                    model_ids.append(str(item["id"]))
        if model_ids:
            self._discovered_model = model_ids[0]
        return model_ids

    def is_healthy(
        self, timeout: float = settings.HEALTH_CHECK_TIMEOUT
    ) -> bool:
        """Check if LM Studio responds on `GET /v1/models` within `timeout` seconds."""
        try:
            self.list_models(timeout=timeout)
            return True
        except requests.RequestException:
            return False
        except ValueError:
            return False

    def resolve_model(
        self, timeout: float = settings.HEALTH_CHECK_TIMEOUT
    ) -> str:
        """Return `LMSTUDIO_MODEL` from `.env`, or the first ID from `/v1/models`."""
        if self.configured_model:
            return self.configured_model
        if self._discovered_model:
            return self._discovered_model
        try:
            models = self.list_models(timeout=timeout)
            if models:
                return models[0]
        except requests.RequestException:
            pass
        return "llama-3.1-8b-instruct"

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = settings.LMSTUDIO_MAX_TOKENS,
        timeout: float = settings.LMSTUDIO_REQUEST_TIMEOUT,
    ) -> str:
        """Send a chat completion request to `POST /v1/chat/completions`."""
        model_id = self.resolve_model()
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "temperature": settings.LMSTUDIO_TEMPERATURE,
            "top_p": settings.LMSTUDIO_TOP_P,
            "top_k": settings.LMSTUDIO_TOP_K,
            "repeat_penalty": settings.LMSTUDIO_REPEAT_PENALTY,
            "max_tokens": max_tokens,
            "stream": False,
        }
        response = requests.post(self.chat_url, json=payload, timeout=timeout)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        choices = data.get("choices", [])
        if not choices or not isinstance(choices, list):
            raise RuntimeError("LM Studio returned an empty choices list.")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LM Studio returned an empty message content.")
        return content.strip()
