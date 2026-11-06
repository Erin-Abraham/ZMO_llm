#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# BMO Robot Project - One-Shot Termux Setup Script (Samsung Galaxy A07)
#
# IMPORTANT PREREQUISITE:
#   Install Termux, Termux:API, and Termux:Boot from F-Droid (NOT Play Store).
#   Grant Microphone permission to Termux:API in Android Settings.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "============================================================"
echo "  BMO Robot - Termux Setup (Samsung Galaxy A07)"
echo "  NOTE: Ensure Termux, Termux:API & Termux:Boot are from F-Droid!"
echo "============================================================"

echo "[1/6] Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "[2/6] Installing python, git, termux-api, and ollama..."
pkg install -y python git termux-api ollama

echo "[3/6] Creating virtual environment and installing Python dependencies..."
cd "${PROJECT_DIR}"
python -m venv .venv
# shellcheck disable=SC1091
source "${PROJECT_DIR}/.venv/bin/activate"
pip install --upgrade pip
pip install requests

echo "[4/6] Starting Ollama temporarily to pull TinyLlama 1.1B Q4..."
if ! pgrep -x "ollama" >/dev/null 2>&1; then
  ollama serve >/dev/null 2>&1 &
  OLLAMA_PID=$!
  sleep 3
else
  OLLAMA_PID=""
fi

ollama pull tinyllama

if [ -n "${OLLAMA_PID}" ]; then
  kill "${OLLAMA_PID}" >/dev/null 2>&1 || true
fi

echo "[5/6] Preparing .env configuration file..."
if [ ! -f "${PROJECT_DIR}/.env" ]; then
  cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
  echo "Created ${PROJECT_DIR}/.env from .env.example (ESP32_ENABLED=false by default)."
  echo ">>> ACTION REQUIRED: Edit .env and set LAPTOP_IP to your Windows laptop Wi-Fi IP! <<<"
fi

echo "[6/6] Installing start_bmo.sh into ~/.termux/boot/ for Termux:Boot..."
mkdir -p "${HOME}/.termux/boot"
cp "${SCRIPT_DIR}/start_bmo.sh" "${HOME}/.termux/boot/start_bmo.sh"
chmod +x "${SCRIPT_DIR}/start_bmo.sh" "${HOME}/.termux/boot/start_bmo.sh"

echo "============================================================"
echo "  Setup complete!"
echo "  1. Edit ${PROJECT_DIR}/.env with your LAPTOP_IP."
echo "  2. Plug in your external mic and verify Termux:API has Microphone permission."
echo "  3. Open the Termux:Boot app once so Android registers boot startup."
echo "  4. Run: bash termux/start_bmo.sh"
echo "  5. Manually open Chrome to http://localhost:8080 and tap for fullscreen."
echo "============================================================"
