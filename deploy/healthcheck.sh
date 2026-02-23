#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="${SERVICE_NAME:-aipidginbot}"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "❌ systemctl not found on this server"
  exit 1
fi

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "✅ Service is active: $SERVICE_NAME"
else
  echo "❌ Service is not active: $SERVICE_NAME"
  sudo systemctl --no-pager --full status "$SERVICE_NAME" | sed -n '1,40p'
  exit 1
fi

echo "--- Last logs ---"
if [ -f "$APP_DIR/bot.log" ]; then
  tail -n 40 "$APP_DIR/bot.log"
else
  echo "No log file yet: $APP_DIR/bot.log"
fi
