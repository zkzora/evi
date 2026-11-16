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
  backup) exec python -m evi.backup create /data/backups ;;
  *)      exec "$@" ;;
esac
