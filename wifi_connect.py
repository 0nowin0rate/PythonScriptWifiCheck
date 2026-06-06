#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyautogui>=0.9",
#   "opencv-python>=4.0",
#   "Pillow>=9.0",
#   "requests>=2.28",
# ]
# ///
"""
Guest WiFi captive-portal auto-connector using image recognition.

Steps each cycle:
  1. Check if already connected — if so, sleep 12 hours.
  2. Click the Firefox icon to open Firefox.
  3. Click the "Open network login page" button in Firefox.
  4. Click the "Connect" button on the Flexential Guest WiFi portal.
  5. Verify connection, then sleep 12 hours.
"""

import logging
import sys
import time
from pathlib import Path

import pyautogui
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONNECTIVITY_TEST_URL = "http://neverssl.com"
CONNECTIVITY_TIMEOUT  = 10   # seconds

# How long to wait for each UI element to appear on screen (seconds)
FIREFOX_OPEN_WAIT        = 4    # after clicking Firefox icon
NETWORK_BTN_WAIT         = 10   # for "Open network login page" to appear
CONNECT_BTN_WAIT         = 10   # for Flexential portal to load
POST_CONNECT_WAIT        = 8    # after clicking Connect, before re-checking

CHECK_INTERVAL_HOURS   = 12
CHECK_INTERVAL_SECONDS = CHECK_INTERVAL_HOURS * 3600

# Confidence threshold for image matching (0–1). Lower = more lenient.
MATCH_CONFIDENCE = 0.80

# Image templates — crop tightly around each element and save as PNG.
IMAGES_DIR          = Path(__file__).parent / "images"
IMG_FIREFOX         = IMAGES_DIR / "firefox_icon.png"
IMG_NETWORK_BTN     = IMAGES_DIR / "open_network_login.png"
IMG_CONNECT_BTN     = IMAGES_DIR / "connect_button.png"
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("wifi_connect.log"),
    ],
)
log = logging.getLogger(__name__)

# Prevent pyautogui from throwing on tiny moves; give it time between actions.
pyautogui.PAUSE = 0.3
pyautogui.FAILSAFE = True   # move mouse to top-left corner to abort


def is_connected() -> bool:
    try:
        r = requests.get(CONNECTIVITY_TEST_URL, timeout=CONNECTIVITY_TIMEOUT,
                         allow_redirects=False)
        return r.status_code == 200
    except requests.RequestException:
        return False


def wait_and_click(image_path: Path, description: str, timeout: int) -> bool:
    """
    Wait up to `timeout` seconds for `image_path` to appear on screen,
    then click its centre. Returns True on success.
    """
    log.info("Looking for: %s (timeout %ds) …", description, timeout)
    deadline = time.time() + timeout
    while time.time() < deadline:
        location = pyautogui.locateOnScreen(
            str(image_path),
            confidence=MATCH_CONFIDENCE,
        )
        if location:
            cx, cy = pyautogui.center(location)
            log.info("Found '%s' at (%d, %d) — clicking …", description, cx, cy)
            pyautogui.click(cx, cy)
            return True
        time.sleep(1)
    log.error("'%s' not found on screen after %ds.", description, timeout)
    return False


def attempt_connect() -> bool:
    # Step 1 — open Firefox
    if not wait_and_click(IMG_FIREFOX, "Firefox icon", timeout=10):
        return False
    time.sleep(FIREFOX_OPEN_WAIT)

    # Step 2 — click "Open network login page"
    if not wait_and_click(IMG_NETWORK_BTN, "Open network login page", timeout=NETWORK_BTN_WAIT):
        return False

    # Step 3 — click "Connect" on the Flexential portal
    if not wait_and_click(IMG_CONNECT_BTN, "Connect button", timeout=CONNECT_BTN_WAIT):
        return False

    log.info("Clicked Connect — waiting %ds for connection …", POST_CONNECT_WAIT)
    time.sleep(POST_CONNECT_WAIT)

    connected = is_connected()
    log.info("Post-click connectivity check: %s", "CONNECTED" if connected else "STILL OFFLINE")
    return connected


def _check_images() -> bool:
    missing = [p for p in (IMG_FIREFOX, IMG_NETWORK_BTN, IMG_CONNECT_BTN) if not p.exists()]
    if missing:
        log.error("Missing template image(s): %s", [str(p) for p in missing])
        log.error("See the README for instructions on how to create them.")
        return False
    return True


def run() -> None:
    if not _check_images():
        sys.exit(1)

    log.info("WiFi auto-connect daemon started (check interval: %dh)", CHECK_INTERVAL_HOURS)
    while True:
        if is_connected():
            log.info("Already connected. Sleeping %dh …", CHECK_INTERVAL_HOURS)
            time.sleep(CHECK_INTERVAL_SECONDS)
        else:
            log.warning("Not connected — starting portal connect sequence …")
            success = attempt_connect()
            if success:
                log.info("Connected successfully. Sleeping %dh …", CHECK_INTERVAL_HOURS)
                time.sleep(CHECK_INTERVAL_SECONDS)
            else:
                log.error("Connection attempt failed. Retrying in 60 s …")
                time.sleep(60)


if __name__ == "__main__":
    run()
