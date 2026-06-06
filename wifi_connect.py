#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyautogui>=0.9",
#   "Pillow>=9.0",
#   "requests>=2.28",
# ]
# ///
"""
Guest WiFi captive-portal auto-connector.

Clicks through the UI using fixed screen coordinates:
  1. Firefox icon
  2. "Open network login page" button in Firefox
  3. "Connect" button on the Flexential Guest WiFi portal

Run find_coords.py once to get the correct X/Y values for your screen,
then paste them into the COORDINATES section below.
"""

import logging
import sys
import time

import pyautogui
import requests

# ---------------------------------------------------------------------------
# Coordinates — run  uv run find_coords.py  to find these for your screen
# ---------------------------------------------------------------------------
FIREFOX_ICON         = (0, 0)   # <-- replace with your values
OPEN_NETWORK_BTN     = (0, 0)   # <-- replace with your values
CONNECT_BTN          = (0, 0)   # <-- replace with your values
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------
FIREFOX_OPEN_WAIT    = 4    # seconds to wait for Firefox to open
NETWORK_BTN_WAIT     = 8    # seconds to wait for the network login button to appear
CONNECT_PAGE_WAIT    = 6    # seconds to wait for the portal page to load
POST_CONNECT_WAIT    = 8    # seconds to wait after clicking Connect

CHECK_INTERVAL_SECONDS = (24 * 3600) + (5 * 60)  # 24 hours and 5 minutes
# ---------------------------------------------------------------------------

CONNECTIVITY_TEST_URL = "http://neverssl.com"
CONNECTIVITY_TIMEOUT  = 10

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

pyautogui.PAUSE    = 0.3
pyautogui.FAILSAFE = True  # move mouse to top-left corner to abort


def is_connected() -> bool:
    try:
        r = requests.get(CONNECTIVITY_TEST_URL, timeout=CONNECTIVITY_TIMEOUT,
                         allow_redirects=False)
        return r.status_code == 200
    except requests.RequestException:
        return False


def click(coords: tuple[int, int], label: str) -> None:
    log.info("Clicking %s at %s", label, coords)
    pyautogui.click(*coords)


def attempt_connect() -> bool:
    # Step 1 — open Firefox
    click(FIREFOX_ICON, "Firefox icon")
    log.info("Waiting %ds for Firefox to open …", FIREFOX_OPEN_WAIT)
    time.sleep(FIREFOX_OPEN_WAIT)

    # Step 2 — click "Open network login page"
    log.info("Waiting %ds for network login button …", NETWORK_BTN_WAIT)
    time.sleep(NETWORK_BTN_WAIT)
    click(OPEN_NETWORK_BTN, "Open network login page")

    # Step 3 — click "Connect"
    log.info("Waiting %ds for portal page to load …", CONNECT_PAGE_WAIT)
    time.sleep(CONNECT_PAGE_WAIT)
    click(CONNECT_BTN, "Connect button")

    log.info("Waiting %ds for connection …", POST_CONNECT_WAIT)
    time.sleep(POST_CONNECT_WAIT)

    connected = is_connected()
    log.info("Connectivity check: %s", "CONNECTED" if connected else "STILL OFFLINE")
    return connected


def _check_coords() -> bool:
    unset = {
        name: val for name, val in [
            ("FIREFOX_ICON", FIREFOX_ICON),
            ("OPEN_NETWORK_BTN", OPEN_NETWORK_BTN),
            ("CONNECT_BTN", CONNECT_BTN),
        ] if val == (0, 0)
    }
    if unset:
        log.error("Coordinates not set: %s", list(unset.keys()))
        log.error("Run  uv run find_coords.py  to find them, then edit wifi_connect.py.")
        return False
    return True


def run() -> None:
    if not _check_coords():
        sys.exit(1)

    log.info("WiFi auto-connect daemon started (check interval: 24h 5m)")
    while True:
        if is_connected():
            log.info("Already connected. Sleeping 24h 5m …")
            time.sleep(CHECK_INTERVAL_SECONDS)
        else:
            log.warning("Not connected — starting connect sequence …")
            success = attempt_connect()
            if success:
                log.info("Connected. Sleeping 24h 5m …")
                time.sleep(CHECK_INTERVAL_SECONDS)
            else:
                log.error("Failed. Retrying in 60 s …")
                time.sleep(60)


if __name__ == "__main__":
    run()
