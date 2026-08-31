#!/usr/bin/env bash
# Start Vision Kled Phase 0 locally (API + admin UI).
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install)
fi

uvicorn src.main:app --reload --host 127.0.0.1 --port "${API_PORT:-8003}" &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT

(cd frontend && npm run dev)
