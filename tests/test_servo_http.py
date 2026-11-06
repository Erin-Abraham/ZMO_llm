"""HTTP gesture test script for the ESP32-C3 servo controller (`tests/test_servo_http.py`).

Checks `GET http://<ESP32_IP>/` and sends each valid gesture (`rest`, `wave`,
`nod`, `shake`, `think`, `happy`, `excited`) via `POST http://<ESP32_IP>/gesture`
with JSON `{"name": "<gesture>"}`. Prints `PASS` or `FAIL`.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


def main() -> int:
    """Send every gesture to the ESP32-C3 over Wi-Fi HTTP and print PASS or FAIL."""
    parser = argparse.ArgumentParser(
        description="Send all BMO servo gestures to the ESP32-C3 HTTP endpoint."
    )
    parser.add_argument(
        "--ip",
        default=settings.ESP32_IP,
        help=f"ESP32-C3 IP address (default from .env: {settings.ESP32_IP})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.6,
        help="Seconds to wait between gestures (default: 1.6s).",
    )
    args = parser.parse_args()

    base_url = f"http://{args.ip}" if settings.ESP32_PORT == 80 else f"http://{args.ip}:{settings.ESP32_PORT}"
    status_url = f"{base_url}/"
    gesture_url = f"{base_url}/gesture"

    print("=== BMO ESP32-C3 Servo HTTP Test ===")
    print(f"Checking status at {status_url} ...")

    try:
        status_resp = requests.get(status_url, timeout=settings.ESP32_TIMEOUT)
        status_resp.raise_for_status()
        print(f"[LIVE] ESP32-C3 status: {status_resp.text}")
    except requests.RequestException as exc:
        print(f"FAIL: Could not reach ESP32-C3 at {status_url} ({exc}).")
        print("      Ensure ESP32-C3 is flashed, powered, and ESP32_IP is set in .env.")
        return 1

    for gesture in settings.VALID_GESTURES:
        print(f"-> Sending POST {gesture_url} with {{\"name\": \"{gesture}\"}} ...")
        try:
            resp = requests.post(
                gesture_url,
                json={"name": gesture},
                timeout=settings.ESP32_TIMEOUT,
            )
            if resp.status_code != 200:
                print(f"FAIL: Gesture '{gesture}' returned HTTP {resp.status_code}: {resp.text}")
                return 1
            print(f"   [OK] Response: {resp.text}")
        except requests.RequestException as exc:
            print(f"FAIL: Request failed for gesture '{gesture}': {exc}")
            return 1
        time.sleep(args.delay)

    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
