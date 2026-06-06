#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyautogui>=0.9", "Pillow>=9.0"]
# ///
"""
Hover your mouse over an element and press Ctrl+C to print its coordinates.
Run this once to find the X/Y for each click target, then paste them into
wifi_connect.py.
"""
import pyautogui, time, signal, sys

def handler(sig, frame):
    x, y = pyautogui.position()
    print(f"\nCoordinates: x={x}, y={y}")
    sys.exit(0)

signal.signal(signal.SIGINT, handler)
print("Move mouse to the target element, then press Ctrl+C to capture coordinates.")
while True:
    x, y = pyautogui.position()
    print(f"  x={x:<5} y={y:<5}", end="\r")
    time.sleep(0.1)
