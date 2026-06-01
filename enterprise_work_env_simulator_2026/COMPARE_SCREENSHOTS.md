# How to see Compare screenshots (visual step diff)

Side-by-side screenshots with **focus box + label** require:

1. Code on `main` with visual diff (merged PR #20+).
2. `./rehearse serve` running.
3. **Two runs** from the **same config** (so step IDs align).
4. At least one **interactive step** (`click`, `fill`, `select`, …) in those runs — `navigate`/`wait` only runs have no focus box.

---

## Steps

### 1. Start API + UI

```bash
cd /path/to/TryLapse
./rehearse serve -o launch-rehearsal/artifacts --port 8765
```

Second terminal:

```bash
cd Frontend_V1 && npm run dev
```

Open http://127.0.0.1:8081/

### 2. Create two comparable runs (with click steps)

Use a config that includes clicks, e.g. extend `lr-self.yaml` or use `examples/enterprise-saas.yaml`:

```bash
./rehearse run -c launch-rehearsal/artifacts/configs/lr-self.yaml \
  -o launch-rehearsal/artifacts
```

Wait for completion; note `run_id` (e.g. `lr-self-20260531-190700`).

Run again (second run):

```bash
./rehearse run -c launch-rehearsal/artifacts/configs/lr-self.yaml \
  -o launch-rehearsal/artifacts
```

Note the second `run_id`.

**Tip:** Change something between runs (fix a UI bug, toggle a feature) so outcomes or URLs differ — otherwise the visual diff section may be empty.

### 3. Open Compare in the dashboard

1. Sidebar → **Compare runs**, or command center top-right **Compare runs** (when ≥2 runs exist).
2. **Run A (baseline):** older run from the dropdown.
3. **Run B (current):** newer run.
4. Scroll to **Visual step diff** (or use `#visual-diff` in the URL).
5. Each changed step is a **collapsible row** — expand one to see side-by-side Run A / Run B PNGs; indigo box = control that was clicked/filled.

### 4. From a run detail page

1. Open a run → **Diff** tab (or header **Diff** link).
2. Same **Visual step diff** panel when comparing to the prior run.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|--------|-----|
| No “Visual step diff” section | No changed steps between runs | Pick enterprise pair or change app between runs; `lr-self` pairs often have 0 changed steps |
| Accordion rows but no focus box | Navigate/wait-only steps | Add `click`/`fill` steps to config and re-run |
| Screenshots but no box | Run captured before focus-region feature | Re-run after upgrading |
| Empty / mock data | API offline | Start `./rehearse serve`; banner should say API live |
| Step IDs don’t match | Different config files | Compare runs from the **same** `*.yaml` |

---

## API check (optional)

```bash
curl -s "http://127.0.0.1:8765/api/diff?a=RUN_A&b=RUN_B" | jq '.visualDiffs[0]'
```

Expect `screenshotPathA`, `screenshotPathB`, and optionally `focusRegionB` with `label`.
