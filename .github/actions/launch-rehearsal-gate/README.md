# Launch Rehearsal Gate

A composite GitHub Action that runs a [Launch Rehearsal](https://github.com/Lapse-AI/TryLapse) staging rehearsal and fails the workflow if the launch gate comes back `CAUTION` or `BLOCKED`.

This is the difference between Launch Rehearsal being a dashboard someone has to remember to check, and being infrastructure a deploy can't skip.

## Usage

```yaml
name: Pre-deploy launch check

on:
  pull_request:
    branches: [main]

jobs:
  launch-rehearsal:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: Lapse-AI/TryLapse/.github/actions/launch-rehearsal-gate@main
        id: rehearsal
        with:
          config: rehearsal.yaml
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}   # optional — omit to run heuristics-only

      - name: Comment gate result on PR
        if: always()
        run: |
          echo "Gate: ${{ steps.rehearsal.outputs.launch-gate }}"
          echo "Readiness: ${{ steps.rehearsal.outputs.readiness }}"
```

The job fails (blocking merge if you've set it as a required check) when the gate is `CAUTION` or `BLOCKED`. Set `fail-on-gate: false` to record the result without blocking.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `config` | yes | — | Path to the rehearsal YAML config, relative to the consuming repo root |
| `repo` | no | `Lapse-AI/TryLapse` | Repo to install the `rehearse` package from |
| `ref` | no | `main` | Git ref of the `rehearse` package to install |
| `python-version` | no | `3.12` | Python version |
| `output-dir` | no | `artifacts` | Where rehearsal artifacts are written |
| `use-llm` | no | `false` | Pass `--llm` to enable persona LLM analysis (needs an LLM API key env var) |
| `fail-on-gate` | no | `true` | Fail the step when the gate is `CAUTION`/`BLOCKED` |

## Outputs

| Output | Description |
|---|---|
| `launch-gate` | `PASS` \| `REVIEW` \| `CAUTION` \| `BLOCKED` |
| `verdict` | One-sentence human-readable verdict |
| `readiness` | Numeric readiness score (0-100) |
| `run-id` | The rehearsal run ID |
| `bundle-path` | Path to the full analysis bundle JSON, for uploading as a build artifact |

## Notes

- This installs `rehearse` directly from the `launch-rehearsal` subdirectory of this monorepo via `pip install git+...#subdirectory=launch-rehearsal`, since the package isn't on PyPI yet. Once it is, this action will switch to a plain `pip install rehearse` and the `repo`/`ref` inputs will become irrelevant (kept for backwards compatibility).
- Without an LLM API key, the rehearsal still runs — findings come from the heuristic engine only. The Gate is computed the same way either way.
- A tool crash (bad config, preflight failure, browser crash) exits non-zero regardless of `fail-on-gate` — that's a setup problem, not a verdict, and should always break the build.
