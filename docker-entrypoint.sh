#!/bin/sh
set -e

# On first start (empty volume), seed demo artifacts from the image.
# Subsequent restarts skip this because .seeded exists.
if [ ! -f /data/artifacts/.seeded ]; then
  echo "First boot — seeding demo artifacts..."
  mkdir -p /data/artifacts
  cp -r /app/demo-artifacts/. /data/artifacts/
  touch /data/artifacts/.seeded
  echo "Seeded."
fi

exec rehearse serve \
  -o /data/artifacts \
  --port "${PORT:-${REHEARSE_PORT:-8080}}" \
  --host 0.0.0.0
