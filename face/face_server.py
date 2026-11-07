"""Tiny offline HTTP server for ZMO's face (`face/`).

Serves `index.html`, `face.css`, and `face.js` from the `face/` directory and
exposes:
- `GET /state`  -> returns JSON `{"state": ..., "emotion": ..., "mode": ...}`
- `POST /state` -> updates any subset of `{state, emotion, mode}` and returns it
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

FACE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = FACE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


class FaceStateStore:
    """Thread-safe holder for ZMO's current face state, emotion, and backend mode."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[str, str] = {
            "state": "idle",
            "emotion": "happy",
            "mode": "laptop",
        }

    def get(self) -> dict[str, str]:
        """Return a shallow copy of the current `{state, emotion, mode}` dict."""
        with self._lock:
            return dict(self._state)

    def update(self, patch: dict[str, Any]) -> dict[str, str]:
        """Validate and apply updates to `{state, emotion, mode}`."""
        with self._lock:
            if "state" in patch and str(patch["state"]) in settings.VALID_FACE_STATES:
                self._state["state"] = str(patch["state"])
            if "emotion" in patch and str(patch["emotion"]) in settings.VALID_EMOTIONS:
                self._state["emotion"] = str(patch["emotion"])
            if "mode" in patch and str(patch["mode"]) in ("laptop", "offline"):
                self._state["mode"] = str(patch["mode"])
            return dict(self._state)


STATE_STORE = FaceStateStore()


class ZMOFaceRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler serving static files in `face/` plus `GET/POST /state`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FACE_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy 300 ms GET /state polling logs; log only errors or changes."""
        if self.path.startswith("/state") and self.command == "GET":
            return
        super().log_message(format, *args)

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/state":
            self._send_json(STATE_STORE.get())
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/state":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object.")
        except (ValueError, UnicodeDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        updated = STATE_STORE.update(payload)
        print(
            f"[face_server] State updated -> state={updated['state']}, "
            f"emotion={updated['emotion']}, mode={updated['mode']}"
        )
        self._send_json(updated)


def run_server(host: str = settings.FACE_HOST, port: int = settings.FACE_PORT) -> None:
    """Start the threaded HTTP server for ZMO's face."""
    server = ThreadingHTTPServer((host, port), ZMOFaceRequestHandler)
    print(f"[face_server] Serving ZMO face at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[face_server] Shutting down face server.")
    finally:
        server.server_close()


def main() -> int:
    """CLI entry point for `face_server.py`."""
    parser = argparse.ArgumentParser(description="Start the ZMO face HTTP server.")
    parser.add_argument("--host", default=settings.FACE_HOST, help="Bind host address.")
    parser.add_argument(
        "--port", type=int, default=settings.FACE_PORT, help="Bind port (default 8080)."
    )
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
