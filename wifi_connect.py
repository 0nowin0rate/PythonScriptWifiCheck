#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "playwright>=1.40",
#   "requests>=2.28",
# ]
# ///
"""
Guest WiFi captive-portal auto-connector.

Runs in a loop: checks internet connectivity every 12 hours.
When offline (captive portal detected), opens Firefox via Playwright,
navigates to a plain HTTP URL so the router redirects to the guest
acceptance page, then clicks the centre of the page to connect.
No credentials needed.
"""

import logging
import subprocess
import sys
import time

import requests
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Configuration — edit these to match your network
# ---------------------------------------------------------------------------
# URL used to verify real internet access (needs DNS — only checked when testing
# whether we're already through the portal).
CONNECTIVITY_TEST_URL = "http://neverssl.com"
CONNECTIVITY_TIMEOUT = 10           # seconds
PORTAL_LOAD_WAIT_MS = 5_000         # ms to wait for guest portal page to render
POST_CLICK_WAIT = 10                # seconds to wait after clicking before re-check
CHECK_INTERVAL_HOURS = 12
CHECK_INTERVAL_SECONDS = CHECK_INTERVAL_HOURS * 3600
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


def _default_gateway() -> str | None:
    """Return the default gateway IP address, or None if it can't be found."""
    try:
        out = subprocess.check_output(["ip", "route"], text=True)
        for line in out.splitlines():
            # e.g. "default via 192.168.1.1 dev wlan0 ..."
            parts = line.split()
            if parts and parts[0] == "default" and "via" in parts:
                return parts[parts.index("via") + 1]
    except (subprocess.SubprocessError, ValueError, IndexError):
        pass
    return None


def is_connected() -> bool:
    """Return True when we can reach the open internet."""
    try:
        r = requests.get(CONNECTIVITY_TEST_URL, timeout=CONNECTIVITY_TIMEOUT, allow_redirects=False)
        return r.status_code == 200
    except requests.RequestException:
        return False


def attempt_connect() -> bool:
    """
    Open Firefox via Playwright, navigate directly to the gateway IP (works
    before DNS is available), wait for the guest portal page, click the centre,
    then return whether connected.
    """
    gateway = _default_gateway()
    if gateway:
        portal_url = f"http://{gateway}"
        log.info("Default gateway detected: %s", gateway)
    else:
        # Fallback — some portals intercept any HTTP request
        portal_url = "http://192.168.1.1"
        log.warning("Could not detect gateway — falling back to %s", portal_url)

    log.info("Opening Firefox to accept guest WiFi portal …")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        try:
            page = browser.new_page()
            # Use commit so we don't wait for full page load (portal may redirect)
            page.goto(portal_url, wait_until="commit")
            log.info("Navigated to %s — waiting %dms for guest portal page …",
                     portal_url, PORTAL_LOAD_WAIT_MS)
            page.wait_for_timeout(PORTAL_LOAD_WAIT_MS)

            log.info("Current URL after load: %s", page.url)

            vw = page.viewport_size
            cx = vw["width"] // 2
            cy = vw["height"] // 2
            log.info("Viewport %dx%d — clicking centre (%d, %d)",
                     vw["width"], vw["height"], cx, cy)
            page.mouse.click(cx, cy)

            log.info("Clicked centre — waiting %ds for connection …", POST_CLICK_WAIT)
            time.sleep(POST_CLICK_WAIT)

            connected = is_connected()
            log.info("Post-click connectivity check: %s",
                     "CONNECTED" if connected else "STILL OFFLINE")
            return connected
        finally:
            browser.close()


def run() -> None:
    log.info("WiFi auto-connect daemon started (check interval: %dh)", CHECK_INTERVAL_HOURS)
    while True:
        if is_connected():
            log.info("Already connected to the internet. Sleeping %dh …", CHECK_INTERVAL_HOURS)
            time.sleep(CHECK_INTERVAL_SECONDS)
        else:
            log.warning("Not connected — attempting guest portal connect …")
            success = attempt_connect()
            if success:
                log.info("Connected successfully. Sleeping %dh …", CHECK_INTERVAL_HOURS)
                time.sleep(CHECK_INTERVAL_SECONDS)
            else:
                log.error("Connection attempt failed. Retrying in 60 s …")
                time.sleep(60)


if __name__ == "__main__":
    run()
