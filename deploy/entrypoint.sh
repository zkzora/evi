#!/bin/sh
# Evi container entrypoint: `api` or `worker`. Both must share ONE local persistent volume at /data
# (SQLite WAL needs a local filesystem; do not use network storage or multiple hosts).
set -eu
mkdir -p "$EVI_DATA_DIR" "$EVI_SOURCES_DIR"
for f in /app/seed-sources/*.pdf; do
  [ -e "$EVI_SOURCES_DIR/$(basename "$f")" ] || cp "$f" "$EVI_SOURCES_DIR/"
done
case "${1:-api}" in
  api)    exec python -m uvicorn evi.api:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 20 ;;
  worker) exec python -m evi.worker ;;
  all)
    # Single-container mode for hosts whose persistent volume attaches to ONE service (e.g. Railway):
    # worker in the background, API in the foreground, SIGTERM forwarded to both (worker releases its lease).
    python -m evi.worker & WORKER=$!
    python -m uvicorn evi.api:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 20 & API=$!
    trap 'kill -TERM $API $WORKER 2>/dev/null; wait $API; wait $WORKER' TERM INT
    while kill -0 $API 2>/dev/null && kill -0 $WORKER 2>/dev/null; do sleep 5; done
    kill -TERM $API $WORKER 2>/dev/null; wait; exit 1 ;;   # one process died: stop both so the platform restarts the container
  backup) exec python -m evi.backup create /data/backups ;;
  *)      exec "$@" ;;
esac
