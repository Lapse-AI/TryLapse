# Launch Rehearsal — dashboard-only image for Railway / Coolify / Render
# Does NOT include Playwright/Chromium — use for "rehearse serve" only.
# Triggers new rehearsal runs locally; this image serves the dashboard UI,
# API (summaries, bundles, compare, chat, config) and pre-seeded demo data.

FROM python:3.12-slim

WORKDIR /app

# System deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Node for the frontend build step
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python package first (layer cache)
COPY launch-rehearsal/ ./launch-rehearsal/
RUN pip install --no-cache-dir ./launch-rehearsal

# Build the frontend and embed it into the Python package static dir
COPY Frontend_V1/ ./Frontend_V1/
RUN cd Frontend_V1 && npm ci --silent && npm run build \
    && cp -r dist/. launch-rehearsal/src/rehearse/dashboard/static/

# Copy demo artifacts (runs/, analysis/, scorecards/, sitemaps/, configs/)
# tracked in git — seeded into the data volume on first start
RUN mkdir -p /app/demo-artifacts
COPY launch-rehearsal/artifacts/ /app/demo-artifacts/

# Entrypoint seeds the volume on first boot, then starts the server
COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

VOLUME ["/data/artifacts"]

# PORT is injected by Railway at runtime; REHEARSE_PORT is the local fallback
ENV REHEARSE_PORT=8080
ENV DEEPSEEK_API_KEY=""
ENV REHEARSE_LLM_API_KEY=""
ENV REHEARSE_EMAIL=""
ENV REHEARSE_PASSWORD=""
# Auth — MUST be set in Railway dashboard before first deploy.
# REHEARSE_JWT_SECRET: 64-char hex string; regenerated each restart if unset
#   (sessions survive restarts only when this is set)
# REHEARSE_API_TOKEN: static bearer token for API access (optional)
# REHEARSE_CORS_ORIGIN: comma-separated list of allowed origins (e.g. https://app.trylapse.com)
ENV REHEARSE_JWT_SECRET=""
ENV REHEARSE_API_TOKEN=""
ENV REHEARSE_CORS_ORIGIN=""

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-${REHEARSE_PORT}}/api/health" || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
