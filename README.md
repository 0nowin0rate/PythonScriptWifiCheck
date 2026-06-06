# WiFi Auto-Connect

Automatically connects to the Flexential Guest WiFi captive portal every 12 hours
using image recognition to click through the UI — no credentials needed.

## How it works

Each cycle the script:
1. Checks internet connectivity — if already connected, sleeps 12 hours.
2. Clicks the **Firefox icon** to open the browser.
3. Clicks the **"Open network login page"** button that appears in Firefox.
4. Clicks the **"Connect"** button on the Flexential portal page.
5. Verifies the connection, then sleeps 12 hours.

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.10+ | |
| [UV](https://docs.astral.sh/uv/) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `scrot` or `gnome-screenshot` | Used by pyautogui to take screenshots |

```bash
sudo apt install scrot
```

## Setup — create the template images (one-time)

The script matches against small cropped screenshots of each button.
You need to create these **once** on your desktop.

1. Take a screenshot of your desktop with the Firefox icon visible:
   ```bash
   scrot /tmp/screen.png
   ```
2. Crop tightly around each element using an image editor (e.g. GIMP, or the
   `convert` command from ImageMagick) and save to the `images/` folder:

   | File | What to crop |
   |---|---|
   | `images/firefox_icon.png` | Just the Firefox icon on your taskbar/desktop |
   | `images/open_network_login.png` | The "Open network login page" button in Firefox |
   | `images/connect_button.png` | The "Connect" button on the Flexential portal |

   The crops should be tight — a few pixels of padding is fine, but don't
   include too much background or matching will fail.

   Quick crop with ImageMagick (adjust geometry as needed):
   ```bash
   sudo apt install imagemagick
   # convert /tmp/screen.png -crop WxH+X+Y images/firefox_icon.png
   ```

3. Verify the images folder looks like this:
   ```
   images/
     firefox_icon.png
     open_network_login.png
     connect_button.png
   ```

## Usage

```bash
chmod +x run.sh
./run.sh
```

UV automatically installs all Python dependencies on first run.

## Running as a background service (systemd)

Create `/etc/systemd/system/wifi-connect.service`:

```ini
[Unit]
Description=Flexential Guest WiFi auto-connect
After=graphical-session.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/pythonscriptwificheck
ExecStart=/path/to/pythonscriptwificheck/run.sh
Restart=on-failure
RestartSec=30
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/YOUR_USERNAME/.Xauthority

[Install]
WantedBy=graphical-session.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wifi-connect
sudo systemctl status wifi-connect
```

## Configuration

Edit the constants at the top of `wifi_connect.py`:

| Variable | Default | Purpose |
|---|---|---|
| `MATCH_CONFIDENCE` | `0.80` | Image match threshold (lower = more lenient) |
| `FIREFOX_OPEN_WAIT` | `4` s | Wait after clicking Firefox before looking for next button |
| `NETWORK_BTN_WAIT` | `10` s | Timeout waiting for "Open network login page" to appear |
| `CONNECT_BTN_WAIT` | `10` s | Timeout waiting for the Connect button to appear |
| `POST_CONNECT_WAIT` | `8` s | Wait after clicking Connect before checking connectivity |
| `CHECK_INTERVAL_HOURS` | `12` | How often to re-check connectivity |

## Logs

All output is written to `wifi_connect.log` in the same directory and also
printed to stdout.
