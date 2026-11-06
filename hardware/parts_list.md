# BMO Robot — Chosen Parts List & Indian Sourcing Guide

Cost is a hard constraint for this build. This list contains **only** the components fixed in the project specification.

---

## 1. Core Compute, Display & Voice (Already Owned)

| Item | Role in BMO | Notes |
|---|---|---|
| **Windows Laptop** (24 GB RAM, NVIDIA GPU 8 GB VRAM) | Main "Big Brain" LLM Server | Runs LM Studio on port `1234` with `Llama 3.1 8B Instruct Q4_K_M` |
| **Samsung Galaxy A07** (4 GB RAM, 64 GB storage) | Face Display, Speaker & Runtime Host | Mounted vertically (portrait). Runs Termux + Termux:API + Termux:Boot (from **F-Droid**) and Chrome (`http://localhost:8080`) |
| **External Microphone** (connected to Galaxy A07) | Voice Input (`termux-speech-to-text`) | Used by Termux:API so BMO hears you clearly from across the desk |

---

## 2. Body Controller & Servos (Not Used — Phone-Only Build)

`ESP32_ENABLED=false` is set by default in `.env.example` and `config/settings.py`. No ESP32-C3 or SG90 servos are needed for this build; BMO expresses all emotions (`happy`, `excited`, `thinking`, `sad`, `sleepy`, `surprised`, `neutral`) and states (`idle`, `listening`, `thinking`, `talking`, `offline`) directly on the animated face display while speaking to you.

---

## 3. Enclosure / Shell

| Stage | Material | Approx. Price (INR) | Where to Buy |
|---|---|---:|---|
| **Prototype Shell** | Rectangular plastic storage container | ₹60 – ₹120 | **D-Mart** (home plasticware section) |
| **Final Shell** | Teal PLA 1.75 mm filament (3D printed from your Blender design) | ₹700 – ₹950 / spool (or ₹300 – ₹600 via local 3D print service like Robu 3D printing) | Robu.in, Numakers (Teal / Turquoise PLA) |
