/**
 * ZMO Face Controller (face.js)
 *
 * - Polls GET /state every 300 ms and updates DOM classes:
 *   * state: idle | listening | thinking | talking | offline
 *   * emotion: happy | excited | sad | sleepy | surprised | neutral | thinking
 *   * mode: laptop | offline
 * - Performs natural eye blinks every 3 to 6 seconds.
 * - Supports responsive auto-scaling for Samsung Pop-Up View & landscape.
 * - Supports native Picture-in-Picture (PiP) via floating canvas/video overlay.
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
  const pipBtn = document.getElementById("pip-btn");
  const pipCanvas = document.getElementById("pip-canvas");
  const pipVideo = document.getElementById("pip-video");

  let currentState = "idle";
  let currentEmotion = "happy";
  let currentMode = "laptop";
  let blinkTimerId = null;
  let isBlinking = false;
  let pipAnimationId = null;

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
      applyFaceState("offline", currentEmotion, "offline");
    }
  }

  function triggerBlink() {
    if (currentEmotion !== "sleepy") {
      isBlinking = true;
      leftEye.classList.add("blinking");
      rightEye.classList.add("blinking");
      setTimeout(() => {
        isBlinking = false;
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
    const delayMs = 3000 + Math.floor(Math.random() * 3000);
    blinkTimerId = setTimeout(triggerBlink, delayMs);
  }

  // Tap-to-fullscreen when tapping shell
  if (shell) {
    shell.addEventListener("click", (e) => {
      if (e.target.closest("#pip-btn")) return;
      const docEl = document.documentElement;
      if (!document.fullscreenElement && docEl.requestFullscreen) {
        docEl.requestFullscreen().catch(() => {});
      }
    });
  }

  // --- Picture-in-Picture (PiP) Floating Face Support ---
  function drawPipFrame() {
    if (!pipCanvas) return;
    const ctx = pipCanvas.getContext("2d");
    const w = pipCanvas.width;
    const h = pipCanvas.height;

    // Background teal casing
    ctx.fillStyle = "#5bc2b4";
    ctx.fillRect(0, 0, w, h);

    // Dark screen bezel
    ctx.fillStyle = "#162a28";
    ctx.strokeStyle = "#0e1c1a";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.roundRect(14, 14, w - 28, h - 28, 20);
    ctx.fill();
    ctx.stroke();

    // Offline dot
    if (currentMode === "offline" || currentState === "offline") {
      ctx.fillStyle = "#ff9f1c";
      ctx.beginPath();
      ctx.arc(w - 32, 32, 6, 0, Math.PI * 2);
      ctx.fill();
    }

    // Eyes
    ctx.fillStyle = "#7ef7d4";
    const eyeY = h * 0.42;
    const eyeScaleY = isBlinking || currentEmotion === "sleepy" ? 0.15 : 1.0;

    // Left eye
    ctx.beginPath();
    ctx.ellipse(w * 0.35, eyeY, 14, 24 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.fill();

    // Right eye
    ctx.beginPath();
    ctx.ellipse(w * 0.65, eyeY, 14, 24 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.fill();

    // Blush marks
    ctx.fillStyle = "rgba(255, 141, 161, 0.55)";
    ctx.beginPath();
    ctx.ellipse(w * 0.22, h * 0.62, 16, 8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(w * 0.78, h * 0.62, 16, 8, 0, 0, Math.PI * 2);
    ctx.fill();

    // Mouth
    ctx.strokeStyle = "#7ef7d4";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.beginPath();

    const mouthY = h * 0.65;
    if (currentState === "talking") {
      const mouthHeight = 12 + Math.abs(Math.sin(Date.now() / 120)) * 14;
      ctx.fillStyle = "#2b594f";
      ctx.beginPath();
      ctx.roundRect(w * 0.4, mouthY - 4, w * 0.2, mouthHeight, 10);
      ctx.fill();
      ctx.stroke();
    } else if (currentEmotion === "sad") {
      ctx.arc(w * 0.5, mouthY + 16, 18, Math.PI * 1.15, Math.PI * 1.85, false);
      ctx.stroke();
    } else {
      ctx.arc(w * 0.5, mouthY - 6, 22, Math.PI * 0.15, Math.PI * 0.85, false);
      ctx.stroke();
    }

    pipAnimationId = requestAnimationFrame(drawPipFrame);
  }

  if (pipBtn && pipVideo && document.pictureInPictureEnabled) {
    pipBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        if (document.pictureInPictureElement) {
          await document.exitPictureInPicture();
          if (pipAnimationId) cancelAnimationFrame(pipAnimationId);
          return;
        }

        drawPipFrame();
        const stream = pipCanvas.captureStream(30);
        pipVideo.srcObject = stream;
        await pipVideo.play();
        await pipVideo.requestPictureInPicture();

        pipVideo.addEventListener("leavepictureinpicture", () => {
          if (pipAnimationId) cancelAnimationFrame(pipAnimationId);
        }, { once: true });
      } catch (err) {
        console.warn("PiP not supported or failed:", err);
      }
    });
  } else if (pipBtn && !document.pictureInPictureEnabled) {
    pipBtn.style.display = "none";
  }

  scheduleNextBlink();
  setInterval(pollState, POLL_INTERVAL_MS);
  pollState();
})();
