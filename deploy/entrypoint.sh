#!/bin/sh
# Evi container entrypoint: `api` or `worker`. Both must share ONE local persistent volume at /data
# (SQLite WAL needs a local filesystem; do not use network storage or multiple hosts).
set -eu
mkdir -p "$EVI_DATA_DIR" "$EVI_SOURCES_DIR"
for f in /app/seed-sources/*.pdf; do
  [ -e "$EVI_SOURCES_DIR/$(basename "$f")" ] || cp "$f" "$EVI_SOURCES_DIR/"
done
# First boot: restore the verified release snapshot when the data dir holds NO stored results.
# A database without any version (e.g. created by an earlier boot) is moved aside, never deleted; real state is never touched.
if [ -f /app/seed-snapshot/MANIFEST.json ]; then
  STORED=$(python -c "import sqlite3,sys,os;p=os.path.join(sys.argv[1],'evi.sqlite3');print(sqlite3.connect(p).execute('SELECT COUNT(*) FROM versions').fetchone()[0] if os.path.exists(p) else 0)" "$EVI_DATA_DIR" 2>/dev/null || echo 0)
  if [ "$STORED" = "0" ]; then
    if [ -n "$(ls -A "$EVI_DATA_DIR")" ]; then
      ASIDE="$EVI_DATA_DIR.preseed-$(date -u +%Y%m%dT%H%M%SZ)"; mv "$EVI_DATA_DIR" "$ASIDE"; mkdir -p "$EVI_DATA_DIR"
      echo "moved empty pre-seed state to $ASIDE"
    fi
    python -m evi.backup restore /app/seed-snapshot "$EVI_DATA_DIR" || { echo "snapshot restore failed" >&2; exit 1; }
    echo "restored release snapshot into $EVI_DATA_DIR"
  fi
fi
case "${1:-all}" in
  api)    exec python -m uvicorn evi.api:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 20 ;;
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
