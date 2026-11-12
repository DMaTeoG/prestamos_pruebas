#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Running Django migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Starting server: $*"
exec "$@"
