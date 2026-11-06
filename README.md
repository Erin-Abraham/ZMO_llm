# BMO Robot Project

A low-cost, faithful **BMO** companion robot from *Adventure Time*, built for first-time makers in India.

---

## 1. System Architecture & Fixed Specs

| Component | Specification |
|---|---|
| **Laptop (Big Brain)** | Windows, 24 GB RAM, NVIDIA GPU (8 GB VRAM) |
| **Main LLM Server** | LM Studio on the laptop, OpenAI-compatible API on port `1234` |
| **Main Model** | `Llama 3.1 8B Instruct Q4_K_M` |
| **LM Studio Settings** | GPU layers `32`, context `4096`, Flash Attention `ON`, GPU KV cache `ON`, temp `0.75`, top-p `0.9`, top-k `40`, repeat penalty `1.1`, max tokens `150`, batch `512` |
| **Phone (Face, Mic & Host)** | Samsung Galaxy A07 (4 GB RAM, 64 GB storage) + external microphone, mounted vertically in portrait orientation |
| **Phone Runtime** | Termux + Termux:API + Termux:Boot (installed from **F-Droid**, not Play Store), Chrome for face display |
| **Fallback LLM** | `TinyLlama 1.1B Q4` via Ollama in Termux (port `11434`), used automatically when the laptop is unreachable |
| **Body Controller / Servos** | None (`ESP32_ENABLED=false`; phone-only build focused on BMO's animated face and LLM voice conversation) |
| **Shell** | Prototype in a D-Mart plastic container; final teal PLA 3D print designed in Blender |

---

## 2. Project Layout

```text
bmo-robot/
├── README.md
├── PROJECT_STATUS.md              # Audit result + phase tracker + next steps
├── requirements.txt               # Laptop and Termux Python deps, split by comment
├── .env.example                   # LAPTOP_IP, ports, model names (never commit .env)
├── .gitignore
├── config/
│   ├── settings.py                # Loads .env, holds URLs, timeouts, limits
│   └── bmo_system_prompt.txt      # BMO persona prompt
├── brain/
│   ├── llm_router.py              # Health check + automatic fallback + emotion tag extraction
│   ├── lmstudio_client.py         # OpenAI-style client for LM Studio (/v1/models, /v1/chat/completions)
│   ├── ollama_client.py           # /api/chat client for Ollama (/api/tags, /api/chat)
│   ├── conversation.py            # History trimming per backend context size
│   └── bmo_brain.py               # Main loop: listen -> think -> speak -> move
├── voice/
│   ├── stt.py                     # Speech to text (Termux:API on phone, input() fallback)
│   └── tts.py                     # Text to speech (termux-tts-speak on phone, pyttsx3 on laptop)
├── face/
│   ├── index.html                 # Animated BMO face, 20:9 portrait layout
│   ├── face.css
│   ├── face.js                    # States + emotions, polls GET /state every 300 ms
│   └── face_server.py             # Tiny HTTP server: serves face, exposes GET/POST /state
├── firmware/
│   └── esp32_c3_servos/
│       ├── esp32_c3_servos.ino    # Non-blocking servo control + gestures over WiFi HTTP (serial optional)
│       └── secrets.h.example      # WiFi SSID and password template (copy to secrets.h)
├── termux/
│   ├── setup_termux.sh            # One-shot phone setup script
│   └── start_bmo.sh               # Launched by Termux:Boot
├── hardware/
│   ├── parts_list.md              # Chosen parts and Indian sources
│   └── wiring.md                  # ESP32-C3 to SG90 servos + power wiring
├── cad/
│   └── dimensions.md              # Galaxy A07 slot and SG90 pocket dimensions for Blender
├── tests/
│   ├── test_llm_connection.py     # Pings LM Studio and Ollama, prints which is live
│   ├── test_router_fallback.py    # Simulates laptop offline, verifies Ollama fallback
│   └── test_servo_http.py         # Sends each gesture to the ESP32 over HTTP
└── docs/
    └── build_log.md               # Builder's log template
```

---

## 3. Quick Start

### Step 1: Configure `.env`
Copy `.env.example` to `.env` and fill in your network addresses:
```powershell
Copy-Item .env.example .env
```
- Set `LAPTOP_IP` to `127.0.0.1` when testing on the laptop, or your laptop's LAN IPv4 address (from `ipconfig`) when running on the phone.
- Set `ESP32_IP` once your ESP32-C3 connects to Wi-Fi and prints its IP on the Serial Monitor.

### Step 2: Laptop Setup (Windows)
1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Open **LM Studio**, load **Llama 3.1 8B Instruct Q4_K_M**, and configure:
   - GPU Offload: **32 layers**
   - Context Length: **4096**
   - Flash Attention: **ON**
   - GPU KV Cache: **ON**
   - Temperature: **0.75**, Top-P: **0.9**, Top-K: **40**, Repeat Penalty: **1.1**, Max Tokens: **150**, Evaluation Batch Size: **512**
3. Start the Local Server on port **1234** (enable **Serve on Local Network** so the Galaxy A07 can reach it).
4. Verify with:
   ```powershell
   python tests/test_llm_connection.py
   python tests/test_router_fallback.py
   ```

### Step 3: Phone Setup (Samsung Galaxy A07)
1. Install **Termux**, **Termux:API**, and **Termux:Boot** from **F-Droid** (do **not** use the Google Play Store versions).
2. Grant Termux:API microphone permissions in Android Settings.
3. Clone or copy this repository into Termux and run:
   ```bash
   bash termux/setup_termux.sh
   ```
4. Edit `.env` with your laptop's Wi-Fi IP (`LAPTOP_IP`) and `ESP32_IP`.
5. Run `bash termux/start_bmo.sh`, then manually open **Chrome** on the phone to `http://localhost:8080` and tap the face to enter full-screen mode.

### Step 4: ESP32-C3 Servo Link
- **Default Transport (Wi-Fi HTTP)**: The brain sends `POST http://<ESP32_IP>/gesture` with JSON `{"name": "wave"}`.
- **Experimental USB OTG Serial Route**: `esp32_c3_servos.ino` also listens on USB Serial (`115200` baud) for line commands such as `GESTURE wave` or `SERVO 90 90 90 90`. This serial fallback is **experimental** because Android/Termux lacks native USB serial device permissions without root or custom Termux:API USB wrappers. Use Wi-Fi HTTP as the primary link.
