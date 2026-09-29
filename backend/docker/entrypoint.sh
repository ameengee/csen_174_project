#!/usr/bin/env bash
set -e

echo "Container entrypoint starting..."

: "${APP_ENV:?APP_ENV must be set (e.g. local, prod)}"

echo "APP_ENV=${APP_ENV}"

# ---- Hand off to actual command ----
exec "$@"
