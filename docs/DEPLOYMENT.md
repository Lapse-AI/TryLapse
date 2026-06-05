# Deployment Runbook

## Architecture overview

One Docker image serves both the Python API and the pre-built React SPA.  
Data is persisted in a single volume mounted at `/data/artifacts`.

```
┌─────────────────────────────────┐
│  Docker container               │
│                                 │
│  ┌──────────────────────────┐   │
│  │  Python HTTP server      │   │
│  │  (ThreadingHTTPServer)   │   │
│  │  :8080                   │   │
│  │                          │   │
│  │  GET /static/* → SPA     │   │
│  │  POST /auth/*  → auth    │   │
│  │  GET|POST /api/* → API   │   │
│  └──────────────────────────┘   │
│                                 │
│  /data/artifacts/               │
│  ├── jobs.db    (SQLite)        │
│  ├── runs/      (JSON evidence) │
│  ├── analysis/  (JSON bundles)  │
│  └── configs/   (YAML)         │
└─────────────────────────────────┘
```

---

## Railway (recommended)

### First deploy

1. Push your code to GitHub.
2. In Railway, click **New Project → Deploy from GitHub repo**.
3. Railway auto-detects the `Dockerfile`.
4. Set environment variables (see table below).
5. Add a **Volume** mounted at `/data/artifacts` so runs persist across deploys.
6. Railway injects `PORT` automatically — no changes needed.

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REHEARSE_JWT_SECRET` | **Yes (prod)** | 64-char hex string. Generate: `openssl rand -hex 32`. All tokens are invalidated if this changes. |
| `REHEARSE_API_TOKEN` | Recommended | Static token to protect all `/api/*` routes. Leave unset to allow open access. |
| `DEEPSEEK_API_KEY` | Optional | Enables AI-powered analysis and chat. |
| `OPENAI_API_KEY` | Optional | OpenAI fallback if DeepSeek is unavailable. |
| `REHEARSE_LLM_API_KEY` | Optional | Generic OpenAI-compatible key. |
| `REHEARSE_LLM_BASE_URL` | Optional | Custom LLM endpoint (e.g. NVIDIA NIM). |
| `REHEARSE_LLM_MODEL` | Optional | Model name override (e.g. `deepseek-chat`). |
| `REHEARSE_EMAIL` | Optional | Email for auth-enabled test configs. |
| `REHEARSE_PASSWORD` | Optional | Password for auth-enabled test configs. |
| `REHEARSE_CORS_ORIGIN` | Optional | Comma-separated allowed CORS origins. Defaults to localhost dev ports. |

### Redeploy

Railway redeploys automatically on every push to the connected branch. The volume at `/data/artifacts` persists across deploys.

### Rollback

In Railway → Deployments, click **Rollback** on any previous deployment. The volume is shared so existing run data is preserved.

---

## Docker Compose (local / self-hosted)

```yaml
# docker-compose.yml
services:
  dashboard:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - artifacts:/data/artifacts
    environment:
      REHEARSE_PORT: 8080
      REHEARSE_JWT_SECRET: "change-me-in-production"
      REHEARSE_API_TOKEN: "change-me-in-production"
      DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY}"
    restart: unless-stopped

volumes:
  artifacts:
```

```bash
docker compose up --build -d
open http://localhost:8080
```

---

## Coolify (self-hosted Railway alternative)

1. Add a new service → **Dockerfile**.
2. Set the same environment variables listed above.
3. Add a persistent volume: source path `/data/artifacts`.
4. Set healthcheck: `curl -f http://localhost:8080/api/health`.

---

## Manual (VPS / bare metal)

```bash
# Install Python deps
cd launch-rehearsal
pip install -e .
playwright install chromium --with-deps

# Build frontend
cd ../Frontend_V1
npm ci && npm run build
cp -r dist/* ../launch-rehearsal/src/rehearse/dashboard/static/

# Run server (background)
REHEARSE_PORT=8080 \
REHEARSE_JWT_SECRET="$(openssl rand -hex 32)" \
rehearse serve --output /data/artifacts --port 8080
```

Use `systemd` or `supervisor` to keep the process alive.

---

## Healthcheck

```
GET /api/health → { "ok": true, "artifacts": "/data/artifacts" }
```

HTTP 200 = healthy. Railway and Coolify both use this endpoint automatically.

---

## Build pipeline

```
Dockerfile
  1. python:3.12-slim base
  2. Install Python deps (pip install -e launch-rehearsal/)
  3. Install Node 20, build Frontend_V1 → static/
  4. Copy demo artifacts (git-tracked JSON/YAML)
  5. ENTRYPOINT docker-entrypoint.sh
       → rehearse serve --output /data/artifacts --port $PORT
```

The frontend build is baked into the image. To update the UI, push a new commit — Railway rebuilds automatically.

---

## Scaling considerations

- The Python HTTP server is `ThreadingHTTPServer` (one thread per request) — adequate for single-team use.
- SQLite with WAL mode handles concurrent reads safely. Avoid running multiple server instances against the same volume.
- Long-running Playwright jobs execute in subprocesses — they are not blocked by the HTTP server thread pool.
- For higher concurrency, replace the HTTP server with uvicorn/FastAPI and the SQLite job queue with Postgres.

---

## Logs

Railway streams stdout/stderr in **Deployments → Logs**.

The server suppresses per-request HTTP logs by default (`log_message` is a no-op). Add `print()` statements inside handler methods for debugging.

---

## Secrets rotation

1. Generate a new `REHEARSE_JWT_SECRET`: `openssl rand -hex 32`.
2. Update it in Railway environment variables.
3. Redeploy. All existing user sessions are invalidated (users must sign in again).
4. Optionally update `REHEARSE_API_TOKEN` in the same deploy.

---

## Backup

The entire state lives in `/data/artifacts`. Back it up with:

```bash
# On Railway: download the volume snapshot from Dashboard → Volume
# On VPS:
tar -czf backup-$(date +%Y%m%d).tar.gz /data/artifacts
```

The `jobs.db` SQLite file contains the jobs queue and user accounts. Run data is in `runs/*.json` and `analysis/*.json` (human-readable, version-controllable).
