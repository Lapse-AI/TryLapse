## Description

## Type of Change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation only
- [ ] Refactor (no behavior change)
- [ ] CI / repo hygiene
- [ ] Tests only

## Related Issues

Closes #
Related to #

## Changes Made

-

## Testing

- [ ] `cd launch-rehearsal && pip install -e ".[dev]" && pytest`
- [ ] `cd launch-rehearsal && rehearse run -c examples/... --dry-run --no-crawl` (if CLI touched)
- [ ] `cd Frontend_V1 && npm ci && npm run lint && npm run build` (if UI touched)
- [ ] Manual demo: `./rehearse serve` + Frontend_V1 (if user-visible)

## Checklist

- [ ] Follows [CONTRIBUTING.md](../CONTRIBUTING.md) (branch name, conventional commits)
- [ ] Updated `CHANGES.md` under **[Unreleased]** when user-visible
- [ ] No secrets committed (`.env` stays local)
- [ ] Scoped diff — no unrelated refactors

## Screenshots / Logs
