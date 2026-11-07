# ZMO Project Status  (updated 2026-11-08)

## Audit
| Path | Status | Note |
|---|---|---|
| `README.md` | Active | Architecture, LM Studio settings, Termux setup, ZMO phone companion |
| `PROJECT_STATUS.md` | Active | Audit report, verification results, phase tracker, and next steps |
| `requirements.txt` | Active | Split by comment into shared (`requests`) and laptop-only (`pyttsx3; sys_platform == "win32"`) |
| `.env.example` | Active | Template for `LAPTOP_IP`, `LMSTUDIO_PORT`, `LMSTUDIO_MODEL`, `OLLAMA_MODEL`, voice pitch/rate |
| `.gitignore` | Active | Protects `.env`, `.venv/`, logs, and wake-word training folders |
| `config/settings.py` | Active | Loads `.env` via `pathlib`, holds all URLs, sampling settings, token budgets, and timeouts |
| `config/zmo_system_prompt.txt` | Active | Exact ZMO persona prompt (sweet, childlike, cheerful companion inspired by BMO) |
| `brain/llm_router.py` | Active | 2 s laptop health check per message, Ollama fallback, mode-change announcements, emotion tag stripping & keyword fallback |
| `brain/lmstudio_client.py` | Active | OpenAI-compatible client using `GET /v1/models` and `POST /v1/chat/completions` |
| `brain/ollama_client.py` | Active | Ollama client using `GET /api/tags` and `POST /api/chat` (`stream: false`, `num_ctx: 1024`, `max_tokens: 80`) |
| `brain/conversation.py` | Active | Preserves system prompt and trims turns to 3000 tokens (laptop) or 600 tokens (Ollama) |
| `brain/zmo_brain.py` | Active | Main loop (`listen -> think -> speak`), updates `/state`, handles wake/sleep cycles |
| `voice/stt.py` | Active | Wraps `termux-speech-to-text` with timeout and `input()` fallback for laptop testing |
| `voice/tts.py` | Active | Wraps `termux-tts-speak` (with tunable `pitch` and `rate`) and `pyttsx3` on Windows laptop |
| `face/index.html` | Active | Futuristic cyan pixel art face, pure screen display, PWA support, Samsung Pop-Up View & landscape optimized |
| `face/face.css` | Active | Glowing neon cyan pixel art styling, cyber HUD header, animated equalizer mouth, and emotion variants |
| `face/face.js` | Active | Polls `GET /state` every 300 ms, natural blinking every 3–6 s, tap-to-fullscreen |
| `face/face_server.py` | Active | Threaded HTTP server serving `face/` and exposing `GET /state` and `POST /state` |
| `face/icon.svg` | Active | Cyan pixel art PWA icon |
| `face/manifest.json` | Active | PWA manifest configured for standalone mode (removes browser URL bar in popup view) |
| `termux/setup_termux.sh` | Active | Installs `python`, `git`, `termux-api`, `ollama`, pulls `tinyllama`, configures `~/.termux/boot/` |
| `termux/start_zmo.sh` | Active | Acquires `termux-wake-lock`, starts `ollama serve`, `face_server.py`, and `zmo_brain.py --standby` |
| `cad/dimensions.md` | Active | Samsung Galaxy A07 slot tolerances and mic clearance for Blender modeling |
| `tests/test_llm_connection.py` | Active | Pings LM Studio (`:1234/v1/models`) and Ollama (`:11434/api/tags`), prints live status and `PASS`/`FAIL` |
| `tests/test_router_fallback.py` | Active | Simulates laptop offline, verifies Ollama selection, mode announcements, emotion parsing, and history trimming |
| `docs/build_log.md` | Active | Builder's log template for recording IPs, measurements, and build notes |

## Current Active Files
- `.gitignore`
- `.env.example`
- requirements.txt`
- `README.md`
- `config/zmo_system_prompt.txt`
- `config/settings.py`
- `brain/conversation.py`
- `brain/lmstudio_client.py`
- `brain/ollama_client.py`
- `brain/llm_router.py`
- `brain/zmo_brain.py`
- `voice/stt.py`
- `voice/tts.py`
- `face/index.html`
- `face/face.css`
- `face/face.js`
- `face/face_server.py`
- `face/icon.svg`
- `face/manifest.json`
- `termux/setup_termux.sh`
- `termux/start_zmo.sh`
- `cad/dimensions.md`
- `tests/test_llm_connection.py`
- `tests/test_router_fallback.py`
- `docs/build_log.md`
- `PROJECT_STATUS.md`

## Verified
- `python -m py_compile config/settings.py brain/conversation.py brain/lmstudio_client.py brain/ollama_client.py brain/llm_router.py brain/zmo_brain.py voice/stt.py voice/tts.py face/face_server.py tests/test_llm_connection.py tests/test_router_fallback.py` -> **PASSED** (exit code 0, zero syntax errors across all Python files).
- `python tests/test_router_fallback.py` -> **PASSED** (`PASS`: verified offline laptop simulation, automatic selection of `ollama`, mode announcements, emotion tag stripping, keyword fallback, and history trimming).
- `face/index.html`, `face/face.css`, `face/face.js` -> **PASSED** (futuristic cyan pixel art redesign, no popup icon, no bottom toy controls, fully responsive in Samsung Pop-Up View and landscape mode).

## Phase tracker
- [x] Phase 1 Brain: LM Studio server running, tests/test_llm_connection.py passes, local Ollama TinyLlama 1.1B fallback tested & operational
- [x] Phase 2 Voice: speech in (external mic) and out on the Galaxy A07 (4 GB / 64 GB) via Termux:API + Standby Mode ('Rise and shine ZMO' wake word & 'Sleep off ZMO' sleep cycle implemented)
- [x] Phase 3 Face: futuristic cyan pixel art face, PWA standalone mode in Samsung Pop-Up View & landscape, zero unwanted icons/colors, reacts to /state
- [ ] Phase 4 Shell: prototype box done, Blender model, final print
