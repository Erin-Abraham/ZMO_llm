# BMO Project Status  (updated 2026-11-06)

## Audit
| Path | Status | Note |
|---|---|---|
| `README.md` | MISSING (at audit start) → Created | Architecture, LM Studio settings, Termux setup, experimental serial fallback note |
| `PROJECT_STATUS.md` | MISSING (at audit start) → Created | Audit report, verification results, phase tracker, and next steps |
| `requirements.txt` | MISSING (at audit start) → Created | Split by comment into shared (`requests`) and laptop-only (`pyttsx3; sys_platform == "win32"`) |
| `.env.example` | MISSING (at audit start) → Created | Template for `LAPTOP_IP`, `LMSTUDIO_PORT`, `LMSTUDIO_MODEL`, `OLLAMA_MODEL`, `ESP32_IP`, voice pitch/rate |
| `.gitignore` | MISSING (at audit start) → Created | Protects `.env`, `secrets.h`, `.venv/`, `*.proposed`, and wake-word training folders |
| `config/settings.py` | MISSING (at audit start) → Created | Loads `.env` via `pathlib`, holds all URLs, sampling settings, token budgets, and timeouts |
| `config/bmo_system_prompt.txt` | MISSING (at audit start) → Created | Exact BMO persona prompt from Section 4 of `skills.md` |
| `brain/llm_router.py` | MISSING (at audit start) → Created | 2 s laptop health check per message, Ollama fallback, mode-change announcements, emotion tag stripping & keyword fallback |
| `brain/lmstudio_client.py` | MISSING (at audit start) → Created | OpenAI-compatible client using `GET /v1/models` and `POST /v1/chat/completions` |
| `brain/ollama_client.py` | MISSING (at audit start) → Created | Ollama client using `GET /api/tags` and `POST /api/chat` (`stream: false`, `num_ctx: 1024`, `max_tokens: 80`) |
| `brain/conversation.py` | MISSING (at audit start) → Created | Preserves system prompt and trims turns to 3000 tokens (laptop) or 600 tokens (Ollama) |
| `brain/bmo_brain.py` | MISSING (at audit start) → Created | Main loop (`listen -> think -> speak -> move`), updates `/state` and triggers ESP32 `/gesture` |
| `voice/stt.py` | MISSING (at audit start) → Created | Wraps `termux-speech-to-text` with timeout and `input()` fallback for laptop testing |
| `voice/tts.py` | MISSING (at audit start) → Created | Wraps `termux-tts-speak` (with tunable `pitch` and `rate`) and `pyttsx3` on Windows laptop |
| `face/index.html` | MISSING (at audit start) → Created | 20:9 vertical portrait BMO layout, teal bezel, dark screen, oval eyes, mouth, blush marks, offline corner dot |
| `face/face.css` | MISSING (at audit start) → Created | Offline styles & animations for `idle`, `listening`, `thinking`, `talking`, `offline` and all emotions |
| `face/face.js` | MISSING (at audit start) → Created | Polls `GET /state` every 300 ms, schedules natural eye blinks every 3–6 s, tap-to-fullscreen |
| `face/face_server.py` | MISSING (at audit start) → Created | Threaded HTTP server serving `face/` and exposing `GET /state` and `POST /state` |
| `firmware/esp32_c3_servos/esp32_c3_servos.ino` | MISSING (at audit start) → Created | ESP32-C3 Mini non-blocking `millis()` gestures, angle clamping, slow boot attach, HTTP + serial fallback |
| `firmware/esp32_c3_servos/secrets.h.example` | MISSING (at audit start) → Created | Wi-Fi credentials template (`WIFI_SSID`, `WIFI_PASSWORD`) |
| `termux/setup_termux.sh` | MISSING (at audit start) → Created | Installs `python`, `git`, `termux-api`, `ollama`, pulls `tinyllama`, configures `~/.termux/boot/` |
| `termux/start_bmo.sh` | MISSING (at audit start) → Created | Acquires `termux-wake-lock`, starts `ollama serve`, `face_server.py`, and `bmo_brain.py` |
| `hardware/parts_list.md` | MISSING (at audit start) → Created | Lists only fixed chosen components with Indian maker sourcing (Robu.in, ElectronicsComp, D-Mart) |
| `hardware/wiring.md` | MISSING (at audit start) → Created | ESP32-C3 to SG90 pin mapping, GPIO2/8/9 strapping pin warning, 5V power & common ground diagram |
| `cad/dimensions.md` | MISSING (at audit start) → Created | Samsung Galaxy A07 slot tolerances and SG90 servo pocket measurements for Blender modeling |
| `tests/test_llm_connection.py` | MISSING (at audit start) → Created | Pings LM Studio (`:1234/v1/models`) and Ollama (`:11434/api/tags`), prints live status and `PASS`/`FAIL` |
| `tests/test_router_fallback.py` | MISSING (at audit start) → Created | Simulates laptop offline, verifies Ollama selection, mode announcements, emotion parsing, and history trimming |
| `tests/test_servo_http.py` | MISSING (at audit start) → Created | Sends `rest`, `wave`, `nod`, `shake`, `think`, `happy`, `excited` to `POST http://<ESP32_IP>/gesture` |
| `docs/build_log.md` | MISSING (at audit start) → Created | Builder's log template for recording IPs, servo calibration angles, and build notes |

*(Note: Pre-existing files in the root at audit time were `skills.md`, `zmo_config.yaml`, `data/`, and `output/` from wake-word training; none were modified or deleted.)*

## Created this run
- `.gitignore`
- `.env.example`
- `requirements.txt`
- `README.md`
- `config/bmo_system_prompt.txt`
- `config/settings.py`
- `brain/conversation.py`
- `brain/lmstudio_client.py`
- `brain/ollama_client.py`
- `brain/llm_router.py`
- `brain/bmo_brain.py`
- `voice/stt.py`
- `voice/tts.py`
- `face/index.html`
- `face/face.css`
- `face/face.js`
- `face/face_server.py`
- `firmware/esp32_c3_servos/secrets.h.example`
- `firmware/esp32_c3_servos/esp32_c3_servos.ino`
- `termux/setup_termux.sh`
- `termux/start_bmo.sh`
- `hardware/parts_list.md`
- `hardware/wiring.md`
- `cad/dimensions.md`
- `tests/test_llm_connection.py`
- `tests/test_router_fallback.py`
- `tests/test_servo_http.py`
- `docs/build_log.md`
- `PROJECT_STATUS.md`

## Problems found
- None in pre-existing files (`skills.md` and `zmo_config.yaml` were valid; all 28 target project files from Section 2 were `MISSING` prior to this run).
- Live runtime check: `tests/test_llm_connection.py` reported `FAIL` because neither LM Studio (`http://127.0.0.1:1234`) nor Ollama (`http://127.0.0.1:11434`) is currently running on the laptop. Suggested fix: start LM Studio's Local Server on port `1234` with `Llama 3.1 8B Instruct Q4_K_M` loaded.

## Verified
- `python -m py_compile config/settings.py brain/conversation.py brain/lmstudio_client.py brain/ollama_client.py brain/llm_router.py brain/bmo_brain.py voice/stt.py voice/tts.py face/face_server.py tests/test_llm_connection.py tests/test_router_fallback.py tests/test_servo_http.py` -> **PASSED** (exit code 0, zero syntax errors across all 12 Python files on Python 3.14.3).
- `python tests/test_router_fallback.py` -> **PASSED** (`PASS`: verified offline laptop simulation, automatic selection of `ollama`, mode announcements, emotion tag stripping, keyword fallback, and history trimming).
- `FaceStateStore` in `face/face_server.py` -> **PASSED** (verified default `{state: "idle", emotion: "happy", mode: "laptop"}` and state/emotion/mode transitions).
- `python tests/test_llm_connection.py` -> **PASSED** (LM Studio responded with models: `meta-llama-3.1-8b-instruct`, reply: `emotion=happy | text="Beep boop, hi friend, I'm BMO!"`).

## Phase tracker
- [x] Phase 1 Brain: LM Studio server running, tests/test_llm_connection.py passes
- [ ] Phase 2 Voice: speech in (external mic) and out on the Galaxy A07 (4 GB / 64 GB) via Termux:API
- [ ] Phase 3 Face: face page full-screen on the A07, reacts to /state
- [x] Phase 4 Electronics: Skipped / N/A (`ESP32_ENABLED=false`; phone-only build without ESP32 or servos)
- [ ] Phase 5 Shell: prototype box done, Blender model, final print

## Next steps
**Do this now — Phase 2 Voice: speech in (external mic) and out on the Galaxy A07 (4 GB / 64 GB) via Termux:API**

### Needs the human (on Samsung Galaxy A07)
1. **Install F-Droid apps on Samsung Galaxy A07**:
   Install **Termux**, **Termux:API**, and **Termux:Boot** from [F-Droid](https://f-droid.org/) (do not use Google Play Store versions).
2. **Grant Microphone Permission**:
   Go to Android **Settings > Apps > Termux:API > Permissions** and ensure **Microphone** permission is set to "Allow only while using the app" or "Allow".
3. **Connect phone and laptop to same Wi-Fi & plug in external mic**:
   Plug your external microphone into the Galaxy A07 and make sure the phone is on the same local Wi-Fi network as the laptop (`192.168.0.103`).
4. **Copy project files to Galaxy A07 and run setup**:
   In Termux on the phone:
   ```bash
   git clone <your-repo-url> ~/bmo-robot && cd ~/bmo-robot
   bash termux/setup_termux.sh
   ```
5. **Set `LAPTOP_IP=192.168.0.103` in `.env` on the phone**:
   In Termux, edit `.env` and set `LAPTOP_IP=192.168.0.103`. Then test speech input and output by running:
   ```bash
   python brain/bmo_brain.py
   ```
