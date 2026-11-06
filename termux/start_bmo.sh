#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# BMO Robot Project - Startup Script (Launched manually or via Termux:Boot)
#
# NOTE: Opening Chrome to http://localhost:8080 is a MANUAL step!
# After starting this script, open Chrome on the Galaxy A07, navigate to
# http://localhost:8080, and tap the screen once to enter fullscreen kiosk mode.
# ============================================================================

set -u

# Resolve project directory whether invoked from repo or ~/.termux/boot/
if [ -f "${HOME}/bmo-robot/brain/bmo_brain.py" ]; then
  PROJECT_DIR="${HOME}/bmo-robot"
elif [ -f "${HOME}/ZMO_Training/brain/bmo_brain.py" ]; then
  PROJECT_DIR="${HOME}/ZMO_Training"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

cd "${PROJECT_DIR}" || exit 1

echo "[BMO] Acquiring Termux wake lock..."
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock
fi

# Activate virtual environment if present
if [ -f "${PROJECT_DIR}/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.venv/bin/activate"
fi

echo "[BMO] Starting Ollama fallback server in the background (port 11434)..."
if ! pgrep -x "ollama" >/dev/null 2>&1; then
  nohup ollama serve >"${PROJECT_DIR}/ollama.log" 2>&1 &
  sleep 2
fi

echo "[BMO] Starting BMO Face HTTP server in the background (port 8080)..."
pkill -f "face_server.py" >/dev/null 2>&1 || true
nohup python "${PROJECT_DIR}/face/face_server.py" >"${PROJECT_DIR}/face_server.log" 2>&1 &
sleep 1

echo "============================================================"
echo "  ZMO Face server is live at: http://localhost:8080"
echo "  MANUAL STEP: Open Chrome on the phone to http://localhost:8080"
echo "  and tap the ZMO face to enter full-screen mode."
echo "============================================================"

echo "[ZMO] Starting ZMO in Standby Mode (listening for 'Rise and shine ZMO')..."
python "${PROJECT_DIR}/brain/bmo_brain.py" --standby "$@"
