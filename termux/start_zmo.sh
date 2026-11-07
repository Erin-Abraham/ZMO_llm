#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# ZMO Robot Project - Startup Script (Launched manually or via Termux:Boot)
#
# NOTE: Opening Chrome to http://localhost:8080 is a MANUAL step!
# After starting this script, open Chrome or the installed ZMO PWA on the phone
# (http://localhost:8080) to view the futuristic pixel art face.
# ============================================================================

set -u

# Resolve project directory whether invoked from repo or ~/.termux/boot/
if [ -f "${HOME}/ZMO_robot/brain/zmo_brain.py" ]; then
  PROJECT_DIR="${HOME}/ZMO_robot"
elif [ -f "${HOME}/ZMO_Training/brain/zmo_brain.py" ]; then
  PROJECT_DIR="${HOME}/ZMO_Training"
elif [ -f "${HOME}/zmo-robot/brain/zmo_brain.py" ]; then
  PROJECT_DIR="${HOME}/zmo-robot"
elif [ -f "${HOME}/bmo-robot/brain/zmo_brain.py" ]; then
  PROJECT_DIR="${HOME}/bmo-robot"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

cd "${PROJECT_DIR}" || exit 1

echo "[ZMO] Acquiring Termux wake lock..."
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock
fi

# Activate virtual environment if present
if [ -f "${PROJECT_DIR}/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.venv/bin/activate"
fi

echo "[ZMO] Starting Ollama fallback server in the background (port 11434)..."
if ! pgrep -x "ollama" >/dev/null 2>&1; then
  nohup ollama serve >"${PROJECT_DIR}/ollama.log" 2>&1 &
  sleep 2
fi

echo "[ZMO] Starting ZMO Face HTTP server in the background (port 8080)..."
pkill -f "face_server.py" >/dev/null 2>&1 || true
nohup python "${PROJECT_DIR}/face/face_server.py" >"${PROJECT_DIR}/face_server.log" 2>&1 &
sleep 1

echo "============================================================"
echo "  ZMO Face server is live at: http://localhost:8080"
echo "  Open the installed ZMO app or navigate to http://localhost:8080"
echo "  in Chrome to view ZMO's futuristic cyan face!"
echo "============================================================"

echo "[ZMO] Starting ZMO in Standby Mode (listening for 'Rise and shine ZMO')..."
python "${PROJECT_DIR}/brain/zmo_brain.py" --standby "$@"
