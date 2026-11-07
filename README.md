# ZMO Robot Project

A faithful, futuristic companion robot named **ZMO** (pronounced *"ZEEMO"*), inspired by the cheerful personality of BMO from *Adventure Time*, built for everyday companion interaction.

---

## 1. System Architecture & Fixed Specs

| Component | Specification |
|---|---|
| **Laptop (Big Brain)** | Windows, 24 GB RAM, NVIDIA GPU (8 GB VRAM) |
| **Main LLM Server** | LM Studio on the laptop, OpenAI-compatible API on port `1234` |
| **Main Model** | `Llama 3.1 8B Instruct Q4_K_M` |
| **LM Studio Settings** | GPU layers `32`, context `4096`, Flash Attention `ON`, GPU KV cache `ON`, temp `0.75`, top-p `0.9`, top-k `40`, repeat penalty `1.1`, max tokens `150`, batch `512` |
| **Phone (Face, Mic & Host)** | Samsung Galaxy A07 (4 GB RAM, 64 GB storage) + external microphone |
| **Phone Runtime** | Termux + Termux:API + Termux:Boot (installed from **F-Droid**, not Play Store), Chrome / PWA for face display |
| **Fallback LLM** | `TinyLlama 1.1B Q4` via Ollama in Termux (port `11434`), used automatically when the laptop is unreachable |
| **Face Design** | Sleek futuristic neon-cyan pixel art display, responsive to full-screen kiosk, landscape, and Samsung Pop-Up View floating window |
| **Hardware** | Software-only build (`ESP32_ENABLED=false`) focused on ZMO's animated face and LLM voice conversation |

---

## 2. Project Layout

```text
ZMO_robot/
├── README.md
├── PROJECT_STATUS.md              # Audit result + phase tracker + next steps
├── requirements.txt               # Laptop and Termux Python deps
├── .env.example                   # LAPTOP_IP, ports, model names (never commit .env)
├── .gitignore
├── config/
│   ├── settings.py                # Loads .env, holds URLs, timeouts, limits
│   └── zmo_system_prompt.txt      # ZMO persona prompt
├── brain/
│   ├── llm_router.py              # Health check + automatic fallback + emotion tag extraction
│   ├── lmstudio_client.py         # OpenAI-style client for LM Studio (/v1/models, /v1/chat/completions)
│   ├── ollama_client.py           # /api/chat client for Ollama (/api/tags, /api/chat)
│   ├── conversation.py            # History trimming per backend context size
│   └── zmo_brain.py               # Main loop: listen -> think -> speak
├── voice/
│   ├── stt.py                     # Speech to text (Termux:API on phone, input() fallback)
│   └── tts.py                     # Text to speech (termux-tts-speak on phone, pyttsx3 on laptop)
├── face/
│   ├── index.html                 # Futuristic cyan pixel art face display
│   ├── face.css                   # Glowing neon cyan styling, cyber HUD, responsive Pop-Up View
│   ├── face.js                    # States + emotions, polls GET /state every 300 ms, natural blinking
│   ├── face_server.py             # Tiny HTTP server: serves face, exposes GET/POST /state
│   ├── icon.svg                   # Cyan pixel art PWA icon
│   └── manifest.json              # PWA manifest for standalone floating window
├── termux/
│   ├── setup_termux.sh            # One-shot phone setup script
│   └── start_zmo.sh               # Launched by Termux:Boot with --standby wake-word loop
├── cad/
│   └── dimensions.md              # Galaxy A07 slot and mic clearance for Blender
├── tests/
│   ├── test_llm_connection.py     # Pings LM Studio and Ollama, prints which is live
│   └── test_router_fallback.py    # Simulates laptop offline, verifies Ollama fallback
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
3. In Termux, pull the latest changes:
   ```bash
   git pull origin main
   ```
4. Run:
   ```bash
   bash termux/start_zmo.sh
   ```
5. Open Chrome to `http://localhost:8080`, tap the 3 dots menu and select **"Add to Home screen" / "Install app"**.
   - Open the installed **ZMO** app in **Samsung Pop-Up View** to have ZMO's glowing cyan pixel face float anywhere on your phone screen while you multitask!
6. Wake and Sleep controls:
   - Say **"Rise and shine ZMO"** to wake ZMO up!
   - Say **"Sleep off ZMO"** to put ZMO back into sleeping standby!
