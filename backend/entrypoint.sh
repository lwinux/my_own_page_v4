#!/bin/bash
set -e

echo "[entrypoint] Waiting for postgres to accept connections..."
until alembic upgrade head; do
  echo "[entrypoint] Migration failed (postgres not ready?), retrying in 5s..."
  sleep 5
done

echo "[entrypoint] Starting backend API server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info \
    --access-log
