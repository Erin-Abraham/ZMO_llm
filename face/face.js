/**
 * ZMO Futuristic Face Controller (face.js)
 *
 * - Polls GET /state every 300 ms and updates DOM classes:
 *   * state: idle | listening | thinking | talking | offline
 *   * emotion: happy | excited | sad | sleepy | surprised | neutral | thinking
 *   * mode: laptop | offline
 * - Toggles blinking animation every 3 to 6 seconds.
 * - Displays live backend status in the cyber HUD (Online / Offline).
 * - Tap anywhere on screen to toggle full-screen kiosk view.
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
  const hudStatus = document.getElementById("hud-status");
  const shell = document.getElementById("zmo-shell");

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

    if (hudStatus) {
      if (currentState === "offline" || currentMode === "offline") {
        hudStatus.textContent = "LOCAL [FALLBACK]";
      } else {
        hudStatus.textContent = "ONLINE [BIG BRAIN]";
      }
    }
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
      applyFaceState("offline", currentEmotion, "offline");
    }
  }

  function triggerBlink() {
    if (currentEmotion !== "sleepy") {
      body.classList.add("is-blinking");
      setTimeout(() => {
        body.classList.remove("is-blinking");
      }, 140);
    }
    scheduleNextBlink();
  }

  function scheduleNextBlink() {
    if (blinkTimerId !== null) {
      clearTimeout(blinkTimerId);
    }
    const delayMs = 3000 + Math.floor(Math.random() * 3000);
    blinkTimerId = setTimeout(triggerBlink, delayMs);
  }

  // Tap-to-fullscreen anywhere on screen
  if (shell) {
    shell.addEventListener("click", () => {
      const docEl = document.documentElement;
      if (!document.fullscreenElement && docEl.requestFullscreen) {
        docEl.requestFullscreen().catch(() => {});
      } else if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    });
  }

  scheduleNextBlink();
  setInterval(pollState, POLL_INTERVAL_MS);
  pollState();
})();
