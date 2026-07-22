# Launch Rehearsal — full image for Railway / Coolify / Render
# Includes Playwright + Chromium so hosted users can trigger real
# rehearsal runs from the dashboard, not just browse pre-seeded data.

FROM python:3.12-slim

WORKDIR /app

# System deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Node 22 for the frontend build step (packages require >=22.12.0)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (editable install so the running package reads from /app/launch-rehearsal/src)
# This means static files added after npm build are immediately visible — no re-install needed.
COPY launch-rehearsal/ ./launch-rehearsal/
RUN mkdir -p launch-rehearsal/src/rehearse/dashboard/static
RUN pip install --no-cache-dir -e ./launch-rehearsal

# Chromium + WebKit + Firefox for Playwright — hosted runs can rehearse
# against any of the three engines a config's run.browser_engine selects.
# Chromium-only was a real gap: a "mobile Safari" persona was actually
# desktop Chromium with a mobile viewport, never real WebKit rendering.
# --with-deps pulls the system libraries each engine needs on debian-slim.
# Pinned browser path so the binaries survive user/home changes.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN apt-get update \
    && playwright install --with-deps chromium webkit firefox \
    && rm -rf /var/lib/apt/lists/*

# Build the frontend and copy dist directly into the source static dir.
# Because we used -e above, the running package already resolves to this path.
COPY Frontend_V1/ ./Frontend_V1/
RUN cd Frontend_V1 && npm install --no-audit --no-fund && npm run build \
    && cp -r dist/. /app/launch-rehearsal/src/rehearse/dashboard/static/ \
    && MAIN_JS=$(grep -rl "hydrateRoot" /app/launch-rehearsal/src/rehearse/dashboard/static/client/assets/ | head -1 | xargs basename) \
    && STYLES=$(ls /app/launch-rehearsal/src/rehearse/dashboard/static/client/assets/styles-*.css | head -1 | xargs basename) \
    && sed -i "s|</head>|<link rel=\"stylesheet\" href=\"/assets/$STYLES\" /></head>|" /app/launch-rehearsal/src/rehearse/dashboard/static/client/index.html \
    && sed -i "s|</body>|<script type=\"module\" src=\"/assets/$MAIN_JS\"><\/script></body>|" /app/launch-rehearsal/src/rehearse/dashboard/static/client/index.html

# Copy demo artifacts (runs/, analysis/, scorecards/, sitemaps/, configs/)
# tracked in git — seeded into the data volume on first start
RUN mkdir -p /app/demo-artifacts
COPY launch-rehearsal/artifacts/ /app/demo-artifacts/

# Entrypoint seeds the volume on first boot, then starts the server
COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

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
