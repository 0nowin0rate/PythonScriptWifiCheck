#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "selenium>=4.0",
#   "requests>=2.28",
# ]
# ///
"""
Guest WiFi captive-portal auto-connector.

Runs in a loop: checks internet connectivity every 12 hours.
When offline (captive portal detected), opens Firefox, navigates to a
plain HTTP URL so the router redirects to the guest acceptance page, then
clicks the centre of the page to accept and connect — no credentials needed.
"""

import logging
import sys
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

# ---------------------------------------------------------------------------
# Configuration — edit these to match your network
# ---------------------------------------------------------------------------
CHECK_URL = "http://neverssl.com"          # plain HTTP so captive portals intercept it
CONNECTIVITY_TEST_URL = "http://neverssl.com"
CONNECTIVITY_TIMEOUT = 10                  # seconds
LOGIN_PAGE_LOAD_WAIT = 5                   # seconds to let the login page render
POST_CLICK_WAIT = 10                       # seconds to wait after clicking before re-check
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
        # A captive portal typically redirects; a real response means we're through.
        return r.status_code == 200
    except requests.RequestException:
        return False


def click_centre_of_page(driver: webdriver.Firefox) -> None:
    """Click the geometric centre of whatever page is currently loaded."""
    width = driver.execute_script("return document.documentElement.scrollWidth")
    height = driver.execute_script("return document.documentElement.scrollHeight")
    centre_x = width // 2
    centre_y = height // 2
    log.info("Page size %dx%d — clicking centre (%d, %d)", width, height, centre_x, centre_y)
    ActionChains(driver).move_by_offset(centre_x, centre_y).click().perform()


def attempt_login() -> bool:
    """
    Open Firefox, navigate to CHECK_URL (which should redirect to the guest
    acceptance page), click the centre to accept, then return whether connected.
    """
    log.info("Opening Firefox to accept guest WiFi portal …")
    options = Options()
    # Remove the line below if you want to watch the browser window open.
    # options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    try:
        driver.get(CHECK_URL)
        log.info("Navigated to %s — waiting %ds for guest portal page …", CHECK_URL, LOGIN_PAGE_LOAD_WAIT)
        time.sleep(LOGIN_PAGE_LOAD_WAIT)

        current_url = driver.current_url
        log.info("Current URL after load: %s", current_url)

        click_centre_of_page(driver)
        log.info("Clicked centre — waiting %ds for connection …", POST_CLICK_WAIT)
        time.sleep(POST_CLICK_WAIT)

        connected = is_connected()
        log.info("Post-click connectivity check: %s", "CONNECTED" if connected else "STILL OFFLINE")
        return connected
    finally:
        driver.quit()


def run() -> None:
    log.info("WiFi auto-connect daemon started (check interval: %dh)", CHECK_INTERVAL_HOURS)
    while True:
        if is_connected():
            log.info("Already connected to the internet. Sleeping %dh …", CHECK_INTERVAL_HOURS)
            time.sleep(CHECK_INTERVAL_SECONDS)
        else:
            log.warning("Not connected — attempting captive-portal login …")
            success = attempt_login()
            if success:
                log.info("Login succeeded. Sleeping %dh …", CHECK_INTERVAL_HOURS)
                time.sleep(CHECK_INTERVAL_SECONDS)
            else:
                log.error("Login attempt failed. Retrying in 60 s …")
                time.sleep(60)


if __name__ == "__main__":
    run()
