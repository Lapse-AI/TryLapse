# Launch Rehearsal — Frontend (V1)

Monitoring UI wired to the **real** `rehearse serve` API (not mock-only when the API is up).

## Prerequisites

1. Artifacts from CLI runs under `launch-rehearsal/artifacts/`
2. API server running:

```bash
cd /path/to/TryLapse
./rehearse serve -o launch-rehearsal/artifacts
# → http://127.0.0.1:8765 (or next free port)
```

Optional: backfill analysis bundles for older runs:

```bash
./rehearse backfill -o launch-rehearsal/artifacts
```

## Dev server

```bash
cd Frontend_V1
npm install
npm run dev
```

Vite proxies `/api` and `/files` to `http://127.0.0.1:8765` (see `vite.config.ts`).

When `GET /api/health` succeeds, all pages use live run summaries, bundles, diffs, and screenshots. Otherwise they fall back to mock data.

## Override API URL

```bash
VITE_REHEARSE_API=http://127.0.0.1:8768 npm run dev
```

Use this if `rehearse serve` bound to a port other than 8765.
