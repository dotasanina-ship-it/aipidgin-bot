#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ ! -f ".env" ]; then
  echo "[ERROR] .env file not found. Create from .env.example"
  exit 1
fi

python -m py_compile bot.py
exec python bot.py
