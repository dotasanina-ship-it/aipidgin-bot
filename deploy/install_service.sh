#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="${SERVICE_NAME:-aipidginbot}"
SERVICE_USER="${SERVICE_USER:-$(whoami)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
UNIT_TEMPLATE="$APP_DIR/deploy/aipidginbot.service.template"
UNIT_TARGET="/etc/systemd/system/${SERVICE_NAME}.service"

echo "[1/6] Checking prerequisites"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python not found: $PYTHON_BIN"
  exit 1
fi
if [ ! -f "$APP_DIR/.env" ]; then
  echo "[ERROR] Missing .env in $APP_DIR"
  echo "Copy .env.example to .env and set BOT_TOKEN"
  exit 1
fi
if [ ! -f "$UNIT_TEMPLATE" ]; then
  echo "[ERROR] Missing unit template: $UNIT_TEMPLATE"
  exit 1
fi

echo "[2/6] Creating/updating virtual environment"
if [ ! -d "$APP_DIR/.venv" ]; then
  "$PYTHON_BIN" -m venv "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[3/6] Running syntax check"
"$APP_DIR/.venv/bin/python" -m py_compile "$APP_DIR/bot.py"

echo "[4/6] Installing systemd unit"
sudo mkdir -p /etc/systemd/system
sed \
  -e "s|{{APP_DIR}}|$APP_DIR|g" \
  -e "s|{{SERVICE_USER}}|$SERVICE_USER|g" \
  "$UNIT_TEMPLATE" | sudo tee "$UNIT_TARGET" >/dev/null

echo "[5/6] Enabling and starting service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "[6/6] Service status"
sudo systemctl --no-pager --full status "$SERVICE_NAME" | sed -n '1,20p'

echo
echo "✅ Done. Bot will auto-start after reboot and auto-restart on crashes."
echo "Logs: tail -f $APP_DIR/bot.log"
