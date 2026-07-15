# Launch Rehearsal — Frontend

**Dev and Vision both ship the same newest (Vision-level) UI** at http://127.0.0.1:8081/

| Command              | Badge  | Use                                 |
| -------------------- | ------ | ----------------------------------- |
| `npm run dev`        | Dev    | Daily development                   |
| `npm run dev:vision` | Vision | Same UI — reference / design builds |

See [`UI_PRODUCT_LINES.md`](../enterprise_work_env_simulator_2026/UI_PRODUCT_LINES.md).

## Quick start

```bash
./rehearse serve -o launch-rehearsal/artifacts
cd Frontend_V1 && npm install && npm run dev
# → http://127.0.0.1:8081/
```

When API is offline, both modes show Acme mock so the full UI stays visible. With API live, both use real runs.

**NLU panels (digest, trends insight, run narrative, compare “What changed”, run chat)** appear in **both** dev and Vision. Mock fallbacks in `src/lib/mock-data/store.ts` keep those panels populated when `./rehearse serve` is not running.
