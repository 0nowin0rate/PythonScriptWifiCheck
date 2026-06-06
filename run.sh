#!/usr/bin/env bash
# Run the WiFi auto-connect script with UV.
# Usage:  ./run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# uv run handles dependency installation automatically via the inline metadata.
exec uv run "$SCRIPT_DIR/wifi_connect.py" "$@"
