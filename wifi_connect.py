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
import sys
import time

import requests
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Configuration — edit these to match your network
# ---------------------------------------------------------------------------
# The Arista captive portal controller IP (uamip). Navigating here always
# serves a fresh guest acceptance page regardless of changing challenge tokens.
PORTAL_URL = "http://192.0.2.254"
# URL used to verify real internet access after accepting the portal.
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


def is_connected() -> bool:
    """Return True when we can reach the open internet."""
    try:
        r = requests.get(CONNECTIVITY_TEST_URL, timeout=CONNECTIVITY_TIMEOUT, allow_redirects=False)
        return r.status_code == 200
    except requests.RequestException:
        return False


def attempt_connect() -> bool:
    """
    Open Firefox via Playwright, navigate to the Arista captive portal
    controller (PORTAL_URL), click the centre to accept, then return
    whether connected.
    """
    log.info("Opening Firefox to accept guest WiFi portal …")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        try:
            page = browser.new_page()
            # Use commit so we don't wait for full page load (portal may redirect)
            page.goto(PORTAL_URL, wait_until="commit")
            log.info("Navigated to %s — waiting %dms for guest portal page …",
                     PORTAL_URL, PORTAL_LOAD_WAIT_MS)
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
