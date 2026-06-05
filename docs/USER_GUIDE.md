# User Guide

TryLapse (Launch Rehearsal) runs synthetic end-to-end tests against your product URLs and turns the results into an actionable readiness score — no Selenium grid, no cloud accounts required.

---

## Getting started

### 1. Sign up / sign in

Open the dashboard and click **Sign in** in the top-right product switcher. Create an account with your email and a password — this stores your account in the local database and issues a session token valid for 30 days.

> Signing in is optional if `REHEARSE_API_TOKEN` is not set (local dev mode). When it is set, sign-in is required.

---

### 2. Pick a product scope

The **product switcher** (top-right, flask icon) scopes the entire dashboard to one product:

| Scope | What it shows |
|-------|--------------|
| Cal.com | Cal.com OSS runs |
| Argyle | Argyle staging runs |
| Self-test | The rehearsal server itself |
| Staging | Custom staging target |

Switch product at any time — runs, trend charts, and diff comparisons all update instantly.

---

### 3. Write a config (YAML)

A config defines which URL to test, which personas to simulate, and which journeys to walk.

Minimal example:

```yaml
target_url: https://app.example.com
run_id_prefix: example
product_name: Example App
personas:
  - id: evaluator
    name: Evaluator
    role: First-time visitor
    goals:
      - Understand the product value
      - Find the pricing page

journeys:
  - id: j1-land
    title: Landing page
    steps:
      - action: navigate
        url: /

  - id: j2-signup
    title: Signup flow
    steps:
      - action: navigate
        url: /signup
      - action: fill
        label: Email
        value: test@example.com
      - action: fill
        label: Password
        value: password123
      - action: click
        label: Sign up
```

Save it via **Configs → New config** or upload a YAML file directly.

#### Adding auth to a config

```yaml
auth:
  login_path: /login
  email_env: REHEARSE_EMAIL
  password_env: REHEARSE_PASSWORD
  email_label: Email
  password_label: Password
  submit_label: Log in
```

Set `REHEARSE_EMAIL` and `REHEARSE_PASSWORD` in your environment (or Railway variables).

---

### 4. Trigger a run

From the **Runs** page, click **Run** and select a config. The run is queued and executed in the background. You can watch live progress in the run list.

You can also use the CLI directly:

```bash
rehearse run --config artifacts/configs/my-config.yaml --output artifacts/
```

---

### 5. Reading a run result

Each run produces a **readiness score** (0–100) and a breakdown:

| Section | What it contains |
|---------|-----------------|
| **Summary** | Readiness %, duration, step pass/fail counts |
| **Issues** | Blockers and friction points, sorted by severity |
| **Delights** | Positive signals (fast loads, smooth flows) |
| **Persona grades** | A–F grade per simulated persona |
| **Step log** | Every action with outcome, duration, and console errors |
| **Screenshots** | Annotated captures at key steps |

Click any issue to see the exact step, screenshot, and console errors that triggered it.

---

### 6. Compare two runs (diff)

Go to **Compare** and select two run IDs. The diff shows:

- Readiness delta (↑ or ↓)
- Issues that appeared, disappeared, or persisted
- Per-persona grade changes

---

### 7. Cohort runs (reliability)

A **cohort run** executes the same config N times (default 7) with different random seeds and aggregates the results to measure flakiness:

- **High confidence** — spread < 5 pts across all seeds
- **Medium confidence** — spread 5–15 pts
- **Low confidence** — spread > 15 pts (probable flaky UI)

Trigger from **Runs → Cohort run**.

---

### 8. A/B experiments (variant runs)

Compare two configs head-to-head:

1. Go to **Runs → Variant run**
2. Select Config A (control) and Config B (variant)
3. Optionally add a hypothesis: "New nav increases evaluator readiness"
4. Run — both configs execute and a diff report is generated with a verdict: **held**, **regressed**, or **inconclusive**

---

### 9. Persona Studio

The **Persona Studio** panel lets you add, enable/disable, or rewrite personas for any config using a natural-language prompt. Click **Draft persona** to generate one with AI.

---

### 10. Chat about a run

Every run has a **Chat** tab. Ask questions like:

- "Why did the evaluator fail on step 3?"
- "What's causing the checkout blocker?"
- "How does this compare to last week?"

Responses are powered by your configured LLM (DeepSeek, OpenAI, or NVIDIA NIM).

---

### 11. Trends

The **Trends** page shows readiness over time, page count, flake rate, and recurring issues. Use it to track whether a release improved or regressed your product experience.

---

### 12. Workspace settings

Go to **Settings → Workspace** to configure:

- Product name and environment label
- Run retention period (days)
- PII redaction (blurs email/password fields in screenshots)
- Integrations (Slack, Linear, Jira webhooks)

---

## CLI reference

```bash
# Run a config
rehearse run --config path/to/config.yaml --output artifacts/

# Crawl a site and generate a sitemap
rehearse crawl --config path/to/config.yaml --output artifacts/

# Start the dashboard server
rehearse serve --output artifacts/ --port 8765
```

### Environment variables used by the CLI

| Variable | Purpose |
|----------|---------|
| `REHEARSE_EMAIL` | Login email for auth-enabled configs |
| `REHEARSE_PASSWORD` | Login password for auth-enabled configs |
| `DEEPSEEK_API_KEY` | DeepSeek LLM for AI analysis |
| `OPENAI_API_KEY` | OpenAI fallback |
| `REHEARSE_LLM_API_KEY` | Generic OpenAI-compatible key |
| `REHEARSE_LLM_BASE_URL` | Custom LLM endpoint |
| `REHEARSE_LLM_MODEL` | Model name override |
