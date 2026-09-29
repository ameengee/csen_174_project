#!/usr/bin/env bash
set -e

echo "Starting backend FastAPI service..."

if [ "${APP_ENV}" = "local" ]; then
  exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload --reload-dir /app/src
fi

exec uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8000}
