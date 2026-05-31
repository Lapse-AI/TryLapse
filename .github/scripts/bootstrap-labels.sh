#!/usr/bin/env bash
# One-time label setup for Lapse-AI/TryLapse (idempotent).
set -euo pipefail
REPO="${1:-Lapse-AI/TryLapse}"

create_label() {
  local name="$1"
  local color="$2"
  local description="${3:-}"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null || \
    gh label edit "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null || true
}

create_label bug d73a4a "Something is not working"
create_label enhancement a2eeef "New feature or request"
create_label documentation 0075ca "Documentation improvements"
create_label "area/cli" 1d76db "launch-rehearsal engine"
create_label "area/frontend" 5319e7 "Frontend_V1"
create_label "area/docs" c5def5 "Specs and markdown"
create_label "dependencies 0366d6" "Dependency updates"
create_label "github-actions" 000000 "GitHub Actions"
create_label "python" 3776ab "Python"
create_label "frontend" f1e05a "Frontend"
create_label "priority/critical" b60205 "Critical"
create_label "priority/high" e99695 "High priority"
create_label "priority/medium" fbca04 "Medium priority"
create_label "priority/low" 0e8a16 "Low priority"
create_label "size/XS" 3cbf00 "Very small PR"
create_label "size/S" 77e06b "Small PR"
create_label "size/M" fef2c0 "Medium PR"
create_label "size/L" f9d0c4 "Large PR"
create_label "size/XL" d93f0b "Very large PR"

echo "Labels ensured on $REPO"
