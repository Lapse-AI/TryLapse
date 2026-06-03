# Launch Rehearsal — dashboard-only image for Coolify / self-hosted deploy
# Does NOT include Playwright/Chromium — use this for "rehearse serve" only.
# Runs trigger remotely are not supported in this image; this image serves
# the dashboard UI and API (analysis, summaries, config, compare, chat).

FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node for the frontend build step
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python package first (layer cache)
COPY launch-rehearsal/ ./launch-rehearsal/
RUN pip install --no-cache-dir ./launch-rehearsal

# Copy and build the frontend, then embed into the Python package static dir
COPY Frontend_V1/ ./Frontend_V1/
RUN cd Frontend_V1 && npm ci --silent && npm run build
RUN cp -r Frontend_V1/dist/* launch-rehearsal/src/rehearse/dashboard/static/ 2>/dev/null || true

# Artifacts volume — persisted across deploys
RUN mkdir -p /data/artifacts
VOLUME ["/data/artifacts"]

# Environment — override these in Coolify
ENV REHEARSE_PORT=8080
ENV DEEPSEEK_API_KEY=""
ENV REHEARSE_LLM_API_KEY=""

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${REHEARSE_PORT}/api/health || exit 1

CMD ["sh", "-c", "rehearse serve -o /data/artifacts --port ${REHEARSE_PORT} --host 0.0.0.0"]
