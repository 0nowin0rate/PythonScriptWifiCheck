# WiFi Auto-Connect

Automatically handles captive-portal WiFi login on a Desktop PC.  
Every 12 hours it checks whether you are connected; if not it opens Firefox,
navigates to the captive-portal login page, and clicks the centre of the page
to authenticate.

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.10+ | |
| [UV](https://docs.astral.sh/uv/) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Firefox | Must be installed and on `$PATH` |
| geckodriver | Must be on `$PATH` — see below |

### Install geckodriver

```bash
# Ubuntu/Debian
sudo apt install firefox-geckodriver

# Or download manually from https://github.com/mozilla/geckodriver/releases
# and place the binary in /usr/local/bin/
```

## Usage

```bash
chmod +x run.sh
./run.sh
```

UV automatically installs `selenium` and `requests` into an isolated virtual
environment on first run — no manual `pip install` needed.

## Running as a background service (systemd)

Create `/etc/systemd/system/wifi-connect.service`:

```ini
[Unit]
Description=WiFi captive-portal auto-connect
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/PythonScriptWifiCheck
ExecStart=/path/to/PythonScriptWifiCheck/run.sh
Restart=on-failure
RestartSec=30
# Allow the script to open a real Firefox window on your display
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
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
| `CHECK_URL` | `http://neverssl.com` | URL Firefox opens (must be plain HTTP) |
| `CONNECTIVITY_TEST_URL` | `http://neverssl.com` | URL used for the connectivity check |
| `LOGIN_PAGE_LOAD_WAIT` | `5` s | Time to wait for the login page to render |
| `POST_CLICK_WAIT` | `10` s | Time to wait after clicking before re-checking |
| `CHECK_INTERVAL_HOURS` | `12` | How often to re-check connectivity |

## Logs

All output is written to `wifi_connect.log` in the same directory and also
printed to stdout.
