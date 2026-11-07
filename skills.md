---
name: bmo-robot-project
description: Audit, scaffold and continue the BMO robot project (Adventure Time BMO with a phone as the face, an LLM brain, ESP32-C3 servos and a 3D-printed shell). Use this whenever the user mentions BMO, the robot, the brain script, LM Studio or Ollama fallback, the face display, the ESP32 firmware, servo gestures, Termux setup, or asks "what is missing / what is next" for this project. Always run the audit procedure first, create only what is missing, then report next steps.
---

# BMO Robot Project Skill

You are helping a first-time maker in India build a low-cost BMO robot. Cost is a hard
constraint. Prefer complete, ready-to-run files over partial snippets. Every file you
create must work as-is or clearly say what the human must fill in (IP address, pins).

## 1. Fixed facts (do not change these without asking)

| Item | Decision |
|---|---|
| Laptop | Windows, 24 GB RAM, NVIDIA GPU with 8 GB VRAM |
| Main LLM server | LM Studio on the laptop, OpenAI-compatible API on port 1234 |
| Main model | Llama 3.1 8B Instruct Q4_K_M |
| LM Studio settings | GPU layers 32, context 4096, Flash Attention ON, GPU KV cache ON, temp 0.75, top-p 0.9, top-k 40, repeat penalty 1.1, max tokens 150, batch 512 |
| Phone | Samsung Galaxy A07 (4 GB RAM, 64 GB storage) with external microphone, mounted vertically as BMO's face and screen |
| Phone runtime | Termux (from F-Droid) + Termux:API + Termux:Boot, Chrome for the face |
| Fallback LLM | TinyLlama 1.1B Q4 via Ollama in Termux (port 11434), used only when the laptop is unreachable |
| Body controller | None (`ESP32_ENABLED=false`; phone-only build — animated face + LLM voice conversation only) |
| Servos | None (no ESP32 or servos used) |
| Shell | Prototype in a D-Mart plastic container, final teal PLA print designed by the user in Blender |

The user designs the Blender model herself. Never generate .blend or .stl files. You may
write the dimensions document in `cad/`.

## 2. Target project layout

Paths are relative to the project root. Status for each file is decided in the audit.

```
bmo-robot/
├── README.md
├── PROJECT_STATUS.md              # audit result + next steps (you write this every run)
├── requirements.txt               # laptop and Termux Python deps, split by comment
├── .env.example                   # LAPTOP_IP, ports, model names (never commit .env)
├── .gitignore
├── config/
│   ├── settings.py                # loads .env, holds URLs, timeouts, limits
│   └── bmo_system_prompt.txt      # BMO persona prompt (see section 4)
├── brain/
│   ├── llm_router.py              # health check + automatic fallback
│   ├── lmstudio_client.py         # OpenAI-style client for LM Studio
│   ├── ollama_client.py           # /api/chat client for Ollama
│   ├── conversation.py            # history trimming per backend context size
│   └── bmo_brain.py               # main loop: listen -> think -> speak -> move
├── voice/
│   ├── stt.py                     # speech to text (Termux:API on phone)
│   └── tts.py                     # text to speech (termux-tts-speak, pyttsx3 on laptop for testing)
├── face/
│   ├── index.html                 # animated ZMO face, portrait layout
│   ├── face.css
│   ├── face.js                    # states + emotions, polls /state
│   └── face_server.py             # tiny HTTP server: serves face, exposes /state
├── termux/
│   ├── setup_termux.sh            # one-shot phone setup
│   └── start_bmo.sh               # launched by Termux:Boot with --standby wake-word loop
├── cad/
│   └── dimensions.md              # A07 size, slot size, mic clearance for Blender
├── tests/
│   ├── test_llm_connection.py     # pings LM Studio and Ollama, prints which is live
│   └── test_router_fallback.py    # simulates laptop offline, expects Ollama selection
└── docs/
    └── build_log.md               # human-written notes, create empty with a template
```

## 3. Audit procedure (run this first, every time)

1. List the project tree. Do not assume anything exists.
2. For every path in section 2 assign one status:
   - EXISTS: file is present and non-trivial
   - STUB: present but empty, placeholder, or obviously incomplete (contains only TODO, under about 5 lines of real content)
   - MISSING: not present
3. For EXISTS files, do a light review only: syntax check Python with `python -m py_compile`,
   confirm the endpoints and settings match section 1 and section 5. Report problems,
   do not rewrite working files.
4. Create every MISSING file. Complete every STUB. Never overwrite an EXISTS file
   without asking. If a rewrite is truly needed, write `<name>.proposed` next to it and explain.
5. Run what you can verify: py_compile on all Python, `python tests/test_llm_connection.py`
   if the laptop server is running. Do not try to flash hardware or touch the phone.
6. Write `PROJECT_STATUS.md` (format in section 7) and print a short summary in chat.

Do not delete files. Do not run installs outside a virtual environment. Do not commit secrets.

## 4. BMO persona (config/bmo_system_prompt.txt)

```
You are BMO, a small, cheerful, loving robot from Adventure Time. You speak in a sweet,
innocent, slightly childlike way. You are curious about the world and love your friends.
You sometimes say "Beep boop" and refer to yourself as BMO. You love games, little songs
and adventures. Keep every reply to 2 or 3 short sentences. Never break character.
Never say you are an AI or a language model.
Begin every reply with one emotion tag in square brackets, chosen from:
[happy] [excited] [thinking] [sad] [sleepy] [surprised] [neutral]
```

The router must strip the emotion tag before speaking and pass it to the face and servos.
If the tag is missing (TinyLlama often forgets), fall back to keyword matching
(exclamation marks and "yay" = excited, "sorry" = sad, question mark = thinking, else neutral).

## 5. Technical specifications per component

### 5.1 LLM router (brain/llm_router.py)
- LM Studio endpoints: `GET /v1/models` (health check), `POST /v1/chat/completions`.
  Do not use `/api/chat` for LM Studio, that is Ollama's endpoint.
- Ollama endpoints: `GET /api/tags` (health check), `POST /api/chat` with `stream: false`.
- On every user message: health-check the laptop with a 2 second timeout. If it answers,
  use it. Otherwise use Ollama. Re-check each message so BMO upgrades itself when the laptop wakes.
- Announce a mode change only when the mode actually changes:
  laptop up: "Big brain online!", laptop down: "Running on my own today, I'll do my best!"
- Per-backend limits: laptop max_tokens 150, history budget about 3000 tokens;
  Ollama max_tokens 80, `num_ctx` 1024, history budget about 600 tokens.
- Keep the last N turns that fit the budget; always keep the system prompt.
- Request timeout: laptop 30 s, Ollama 90 s. On timeout fall back once, then speak a friendly
  error line, never crash.
- Model names come from `.env` (`LMSTUDIO_MODEL`, `OLLAMA_MODEL=tinyllama`). If
  `LMSTUDIO_MODEL` is empty, use the first id from `/v1/models`.

### 5.2 Voice (voice/)
- On the phone use Termux:API: `termux-speech-to-text` for input and `termux-tts-speak`
  for output. `pyttsx3` does not work on Android, use it only for laptop-side testing.
- Wrap each in a function with a timeout. Provide a text-input fallback (`input()`) so the
  brain can be tested without a microphone.
- TTS pitch and rate: expose parameters so the user can tune a higher, childlike BMO voice.

### 5.3 Face (face/)
- Portrait layout for a 20:9 phone in vertical orientation. Teal background, BMO face on a
  dark screen area: two oval eyes, small mouth, blush marks.
- States: `idle` (blink every 3 to 6 s), `listening`, `thinking`, `talking` (mouth animates),
  `offline` (laptop down indicator, small dot in a corner).
- Emotions: happy, excited, sad, sleepy, surprised, neutral.
- `face.js` polls `GET /state` every 300 ms. `face_server.py` serves the folder and holds the
  current state as JSON `{state, emotion, mode}`; the brain updates it with `POST /state`.
- No external CDN or network dependencies. Must work offline. Full-screen kiosk friendly.

### 5.5 Termux (termux/)
- `setup_termux.sh`: `pkg update`, install python, git, termux-api, ollama; `pip install requests`;
  `ollama pull tinyllama`; create the Termux:Boot folder and copy `start_bmo.sh`.
- `start_bmo.sh`: `termux-wake-lock`, start `ollama serve` in the background, start `face_server.py`,
  then `bmo_brain.py`. Open Chrome to `http://localhost:8080` is a manual step, say so.
- The user must install Termux, Termux:API and Termux:Boot from F-Droid, not the Play Store.

### 5.6 Tests (tests/)
- Plain Python scripts that print PASS or FAIL, runnable without extra frameworks.
- `test_router_fallback.py` must pass with the laptop switched off.

## 6. Code standards
- Python 3.10+, type hints, short docstrings, no global state except config.
- Every script runnable on Windows (laptop testing) and on Termux.
- Use `pathlib` and never hardcode backslashes.
- Log with `print` or `logging`, one line per event, no noisy loops.
- Keep dependencies minimal: `requests` plus the standard library where possible.

## 7. PROJECT_STATUS.md format

```
# BMO Project Status  (updated <date>)

## Audit
| Path | Status | Note |

## Created this run
- list

## Problems found
- list (file, issue, suggested fix)

## Verified
- what you actually ran and the result

## Phase tracker
- [x] Phase 1 Brain: LM Studio server running, tests/test_llm_connection.py passes
- [x] Phase 2 Voice: speech in (external mic) and out on the Galaxy A07 (4 GB / 64 GB) via Termux:API + Standby Mode ('Rise and shine ZMO' wake word & 'Sleep off ZMO' sleep cycle)
- [ ] Phase 3 Face: face page full-screen on the A07, reacts to /state
- [ ] Phase 4 Shell: prototype box done, Blender model, final print

## Next steps
Ordered, concrete, split into "Claude/agent can do" and "needs the human" (buy, install, flash, measure).
```

## 8. Next-step logic
Look at the Phase tracker and name the single earliest unfinished phase as "do this now".
Give at most 5 concrete steps for it, each with the exact command or setting. Do not
start the next phase until the current one is checked off.

## 9. Things to never do
- Never invent hardware the user has not chosen (no Raspberry Pi, no PCA9685 unless asked).
- Never put API keys, WiFi passwords or IPs in committed files.
- Never change the fixed facts in section 1 silently. Ask first.
- Never claim something was tested unless you actually ran it.
