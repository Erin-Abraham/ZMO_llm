"""Central configuration for the ZMO robot project.

Loads environment variables from `.env` (if present in the project root) using
`pathlib` and the Python standard library, and exposes endpoints, model limits,
sampling parameters, and timeouts defined in `skills.md`.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
ENV_FILE_PATH: Path = PROJECT_ROOT / ".env"
SYSTEM_PROMPT_PATH: Path = PROJECT_ROOT / "config" / "zmo_system_prompt.txt"


def _load_dotenv(env_path: Path) -> None:
    """Parse a simple KEY=VALUE `.env` file into `os.environ` without external deps."""
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(ENV_FILE_PATH)

# ---------------------------------------------------------------------------
# 1. Main LLM Server: LM Studio on the Windows Laptop (OpenAI-compatible API)
# ---------------------------------------------------------------------------
LAPTOP_IP: str = os.getenv("LAPTOP_IP", "127.0.0.1").strip() or "127.0.0.1"
LMSTUDIO_PORT: int = int(os.getenv("LMSTUDIO_PORT", "1234"))
LMSTUDIO_BASE_URL: str = f"http://{LAPTOP_IP}:{LMSTUDIO_PORT}"
LMSTUDIO_MODELS_URL: str = f"{LMSTUDIO_BASE_URL}/v1/models"
LMSTUDIO_CHAT_URL: str = f"{LMSTUDIO_BASE_URL}/v1/chat/completions"

# If empty, LMStudioClient resolves the first model id from GET /v1/models
LMSTUDIO_MODEL: str = os.getenv("LMSTUDIO_MODEL", "").strip()

# Fixed LM Studio inference parameters (Section 1 & Section 5.1)
LMSTUDIO_CONTEXT_LENGTH: int = 4096
LMSTUDIO_HISTORY_TOKEN_BUDGET: int = 3000
LMSTUDIO_MAX_TOKENS: int = 150
LMSTUDIO_TEMPERATURE: float = 0.75
LMSTUDIO_TOP_P: float = 0.9
LMSTUDIO_TOP_K: int = 40
LMSTUDIO_REPEAT_PENALTY: float = 1.1
LMSTUDIO_BATCH_SIZE: int = 512
LMSTUDIO_GPU_LAYERS: int = 32

# ---------------------------------------------------------------------------
# 2. Fallback LLM Server: Ollama in Termux on Samsung Galaxy A07
# ---------------------------------------------------------------------------
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "127.0.0.1").strip() or "127.0.0.1"
OLLAMA_PORT: int = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_BASE_URL: str = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_TAGS_URL: str = f"{OLLAMA_BASE_URL}/api/tags"
OLLAMA_CHAT_URL: str = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "tinyllama").strip() or "tinyllama"

# Fixed Ollama inference parameters (Section 5.1)
OLLAMA_NUM_CTX: int = 1024
OLLAMA_HISTORY_TOKEN_BUDGET: int = 600
OLLAMA_MAX_TOKENS: int = 80
OLLAMA_TEMPERATURE: float = 0.75
OLLAMA_TOP_P: float = 0.9
OLLAMA_TOP_K: int = 40
OLLAMA_REPEAT_PENALTY: float = 1.1

# ---------------------------------------------------------------------------
# 3. Timeouts & Mode Announcements (Section 5.1)
# ---------------------------------------------------------------------------
HEALTH_CHECK_TIMEOUT: float = 2.0
LMSTUDIO_REQUEST_TIMEOUT: float = 30.0
OLLAMA_REQUEST_TIMEOUT: float = 90.0

ANNOUNCEMENT_LAPTOP_UP: str = "Big brain online!"
ANNOUNCEMENT_LAPTOP_DOWN: str = "Running on my own today, I'll do my best!"
FRIENDLY_ERROR_REPLY: str = (
    "Beep boop... my circuits got a little dizzy! Can you say that again?"
)

# ---------------------------------------------------------------------------
# 4. Emotions, States & Gestures (Section 4, 5.3, 5.4)
# ---------------------------------------------------------------------------
VALID_EMOTIONS: tuple[str, ...] = (
    "happy",
    "excited",
    "thinking",
    "sad",
    "sleepy",
    "surprised",
    "neutral",
)

VALID_FACE_STATES: tuple[str, ...] = (
    "idle",
    "listening",
    "thinking",
    "talking",
    "offline",
)

# ---------------------------------------------------------------------------
# 5. Face HTTP Server (Section 5.3)
# ---------------------------------------------------------------------------
FACE_HOST: str = os.getenv("FACE_HOST", "127.0.0.1").strip() or "127.0.0.1"
FACE_PORT: int = int(os.getenv("FACE_PORT", "8080"))
FACE_BASE_URL: str = f"http://{FACE_HOST}:{FACE_PORT}"
FACE_STATE_URL: str = f"{FACE_BASE_URL}/state"
FACE_POLL_INTERVAL_MS: int = 300

# ---------------------------------------------------------------------------
# 6. Voice Configuration (Section 5.2)
# ---------------------------------------------------------------------------
TTS_PITCH: float = float(os.getenv("TTS_PITCH", "1.35"))
TTS_RATE: float = float(os.getenv("TTS_RATE", "1.05"))
STT_TIMEOUT: float = float(os.getenv("STT_TIMEOUT", "12.0"))
TTS_TIMEOUT: float = float(os.getenv("TTS_TIMEOUT", "20.0"))
USE_TEXT_INPUT: bool = os.getenv("USE_TEXT_INPUT", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)


def load_system_prompt() -> str:
    """Read and return the ZMO persona system prompt from `config/zmo_system_prompt.txt`."""
    if SYSTEM_PROMPT_PATH.is_file():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    return (
        "You are ZMO (pronounced Zeemo), a small, cheerful, loving robot inspired by BMO from Adventure Time. "
        "Keep every reply to 2 or 3 short sentences. "
        "Begin every reply with one emotion tag in square brackets, chosen from: "
        "[happy] [excited] [thinking] [sad] [sleepy] [surprised] [neutral]"
    )
