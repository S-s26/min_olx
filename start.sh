#!/usr/bin/env bash
# Production startup script for Render.com (or any Linux PaaS).
# Uses daphne (ASGI) to serve both HTTP and WebSocket traffic.
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Default to daphne for ASGI; gunicorn is kept available for HTTP-only fallback.
if [ -z "$PORT" ]; then export PORT=10000; fi

# Workers formula: ~1 worker per CPU core + 1 (Daphne recommends this).
# -2 for the ASGI lifecycle overhead.
WORKERS="${WEB_CONCURRENCY:-3}"

echo "==> Starting daphne on 0.0.0.0:${PORT} with ${WORKERS} workers"
exec daphne -b 0.0.0.0 -p "${PORT}" --workers "${WORKERS}" mini_olx.asgi:application