/**
 * BMO Face Controller (face.js)
 *
 * - Polls GET /state every 300 ms and updates the DOM classes for:
 *   * state: idle | listening | thinking | talking | offline
 *   * emotion: happy | excited | sad | sleepy | surprised | neutral | thinking
 *   * mode: laptop | offline
 * - Performs natural eye blinks every 3 to 6 seconds when in idle/listening/offline states.
 * - Supports tap-to-fullscreen for kiosk display on the Samsung Galaxy A07.
 */

(function () {
  "use strict";

  const POLL_INTERVAL_MS = 300;
  const VALID_STATES = new Set(["idle", "listening", "thinking", "talking", "offline"]);
  const VALID_EMOTIONS = new Set([
    "happy",
    "excited",
    "thinking",
    "sad",
    "sleepy",
    "surprised",
    "neutral"
  ]);

  const body = document.body;
  const leftEye = document.getElementById("left-eye");
  const rightEye = document.getElementById("right-eye");
  const shell = document.getElementById("bmo-shell");

  let currentState = "idle";
  let currentEmotion = "happy";
  let currentMode = "laptop";
  let blinkTimerId = null;

  function applyFaceState(state, emotion, mode) {
    const nextState = VALID_STATES.has(state) ? state : "idle";
    const nextEmotion = VALID_EMOTIONS.has(emotion) ? emotion : "neutral";
    const nextMode = mode === "offline" ? "offline" : "laptop";

    if (
      nextState === currentState &&
      nextEmotion === currentEmotion &&
      nextMode === currentMode
    ) {
      return;
    }

    currentState = nextState;
    currentEmotion = nextEmotion;
    currentMode = nextMode;

    body.className = `state-${currentState} emotion-${currentEmotion} mode-${currentMode}`;
  }

  async function pollState() {
    try {
      const response = await fetch("/state", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      applyFaceState(
        data.state || "idle",
        data.emotion || "neutral",
        data.mode || "laptop"
      );
    } catch (_err) {
      // If face_server.py is temporarily unreachable, show offline indicator dot
      applyFaceState("offline", currentEmotion, "offline");
    }
  }

  function triggerBlink() {
    if (currentEmotion !== "sleepy") {
      leftEye.classList.add("blinking");
      rightEye.classList.add("blinking");
      setTimeout(() => {
        leftEye.classList.remove("blinking");
        rightEye.classList.remove("blinking");
      }, 150);
    }
    scheduleNextBlink();
  }

  function scheduleNextBlink() {
    if (blinkTimerId !== null) {
      clearTimeout(blinkTimerId);
    }
    // Random interval between 3000 ms (3 s) and 6000 ms (6 s)
    const delayMs = 3000 + Math.floor(Math.random() * 3000);
    blinkTimerId = setTimeout(triggerBlink, delayMs);
  }

  // Toggle fullscreen when the user taps the BMO shell on the phone
  if (shell) {
    shell.addEventListener("click", () => {
      const docEl = document.documentElement;
      if (!document.fullscreenElement && docEl.requestFullscreen) {
        docEl.requestFullscreen().catch(() => {});
      }
    });
  }

  scheduleNextBlink();
  setInterval(pollState, POLL_INTERVAL_MS);
  pollState();
})();
