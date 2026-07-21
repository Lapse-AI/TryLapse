# Deploy-after-peak-hours workflow

`deploy-after-peak-hours.yml` exists because Railway's free tier blocks
CLI/API-triggered deploys 8AM–8PM Pacific. Commits pushed to `main` during
that window sit undeployed until someone manually redeploys once the window
opens. This workflow automates that instead of requiring a human to remember.

## One-time setup: `RAILWAY_TOKEN` secret

1. Open the Railway project dashboard → **Settings → Tokens**.
2. Create a new **Project Token** scoped to the `production` environment.
3. In this GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**.
   - Name: `RAILWAY_TOKEN`
   - Value: the token from step 2.

Without this secret, the workflow fails fast with a clear error instead of
silently no-opping.

## How it fires

Two cron schedules cover both Pacific UTC offsets (GitHub Actions cron is
UTC-only and doesn't shift for daylight saving):

- `5 3 * * *` → 20:05 **PDT** (UTC-7, roughly March–November)
- `5 4 * * *` → 20:05 **PST** (UTC-8, roughly November–March)

Both fire every day, but the job checks the real Pacific clock first and
skips the redundant firing — so only one of the two actually deploys, and
the workflow stays correct across DST changes with no yearly edits.

## Manual trigger

Use **Actions → Deploy to Railway after peak hours → Run workflow** to
deploy immediately without waiting for the schedule (e.g. right after
pushing a critical fix during peak hours, so it's ready the instant the
window opens — or if you've upgraded off the free tier and peak hours no
longer apply).

## What it deploys

`railway redeploy --from-source` — pulls and builds the latest commit on
whatever branch Railway's GitHub source is configured to track (currently
`main`), not just a cached rebuild of the last deployed image.
