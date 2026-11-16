# Evi production image: built React frontend + FastAPI API + durable worker (same image, different command).
# NOT built or run on the preparing machine (Docker was unavailable there); see docs/RELEASE-READINESS.md.

# ---- frontend build
FROM node:24-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY public ./public
# Browser-visible configuration only. Never put provider keys in VITE_ variables.
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# ---- runtime
FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    EVI_DATA_DIR=/data/runs EVI_SOURCES_DIR=/data/sources EVI_STATIC_DIR=/app/dist \
    HF_HOME=/models/huggingface EVI_EXECUTION_ENABLED=false \
    EVI_PUBLIC_EVIDENCE=/app/dist/evidence/experiments.v1.json
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 tini curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --home /app evi
WORKDIR /app/backend
COPY backend/requirements.lock ./requirements.lock
# CPU-only torch wheels (the default PyPI Linux wheels bundle CUDA and are several GB larger).
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.lock
COPY backend/evi ./evi
COPY --from=web /app/dist /app/dist
# Registered public sources are seeded into the volume on first start (see deploy/entrypoint.sh); hashes are verified.
COPY public/sources /app/seed-sources
# Verified release snapshot of stored results (hash manifest inside); restored on first boot into an EMPTY data dir.
COPY data/release-snapshot /app/seed-snapshot
COPY deploy/entrypoint.sh /app/entrypoint.sh
RUN chmod 0555 /app/entrypoint.sh && mkdir -p /data /models && chown -R evi:evi /data /models
USER evi
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/api/v1/health" || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
# Default: API + worker in one container (single-volume hosts such as Railway). Compose passes `api` / `worker` explicitly.
CMD ["all"]
