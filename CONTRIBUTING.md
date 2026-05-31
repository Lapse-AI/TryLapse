# Contributing to TryLapse (Launch Rehearsal)

Thank you for contributing. This repo follows **GitHub Flow**: `main` is always releasable; all changes land via pull request.

## Branching

| Branch pattern | Use |
|----------------|-----|
| `main` | Production-ready; protected |
| `feat/<short-name>` | New features |
| `fix/<short-name>` | Bug fixes |
| `chore/<short-name>` | CI, docs, tooling |
| `test/<short-name>` | Test-only changes |

```bash
git checkout main
git pull origin main
git checkout -b feat/compare-selectors
# ... work ...
git push -u origin feat/compare-selectors
gh pr create --title "feat: wire compare run selectors" --body "..."
```

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new capability
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — tests only
- `chore:` — tooling, CI, deps
- `refactor:` — code change without behavior change

Examples:

```text
feat: add export download handlers on run detail
fix: compare page refetches diff when run B changes
test: cover parallel seed flaky heuristics
chore: add GitHub Actions CI workflow
```

## Pull requests

1. Open PR against `main`.
2. Ensure **CI** passes (Python tests + Frontend lint/build).
3. Update **`CHANGES.md`** under `[Unreleased]` for user-visible changes.
4. Request review; address feedback with new commits (squash merge preferred).
5. Delete branch after merge.

PR title must pass the semantic PR check (same types as commits).

## Local development

### Python CLI (`launch-rehearsal`)

```bash
cd launch-rehearsal
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
rehearse run -c examples/enterprise-authenticated.yaml --dry-run --no-crawl
```

### Frontend (`Frontend_V1`)

```bash
cd Frontend_V1
npm ci
npm run dev
# In another terminal from repo root:
./rehearse serve -o launch-rehearsal/artifacts
```

### Environment

Copy secrets locally only (never commit):

```bash
# repo root .env
REHEARSE_EMAIL=...
REHEARSE_PASSWORD=...
DEEPSEEK_API_KEY=...
```

## Scope authority

- **CEO / product gates:** `enterprise_work_env_simulator_2026/CEO_DECISIONS.md`
- **What to build now:** `enterprise_work_env_simulator_2026/FEATURE_SCOPE.md` §0
- **Design partner demos:** `enterprise_work_env_simulator_2026/DESIGN_PARTNER_CHECKLIST.md`

Observe-only rule: Launch Rehearsal **never** auto-fixes or deploys target applications.

## Releases

1. Bump `launch-rehearsal/pyproject.toml` `version`.
2. Move `[Unreleased]` → `[x.y.z]` in `CHANGES.md` with date.
3. Merge to `main`.
4. Tag and push:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

GitHub Actions `release.yml` creates the GitHub Release from `CHANGES.md`.

## Labels (issues & PRs)

| Label | Meaning |
|-------|---------|
| `bug` | Something broken |
| `enhancement` | Feature request |
| `area/cli` | `launch-rehearsal` engine |
| `area/frontend` | `Frontend_V1` |
| `area/docs` | Specs and markdown |
| `priority/high` | Blocks partner demo or CI |
| `size/S` … `size/XL` | Applied automatically on PRs |

## Questions

Open a GitHub issue using the templates, or refer to `FEATURE_SCOPE.md` for planned work.
