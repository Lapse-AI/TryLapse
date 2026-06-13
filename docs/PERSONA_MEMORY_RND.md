# R&D: Persona Depth + Agent Memory Adaptations
*Sourced from: MiroFish (github.com/666ghj/MiroFish) — 66k star swarm intelligence simulation engine*
*Date: 2026-06-11 | Status: Pre-implementation research*

---

## Background

MiroFish is a swarm intelligence engine that simulates how thousands of AI agents (each with psychological profiles, long-term memory, and behavioral logic) behave in response to real-world events. While its domain is social media simulation — not browser-based product testing — two of its core design patterns directly address known gaps in Launch Rehearsal's persona execution quality.

This document translates those two patterns into concrete LR implementation plans.

---

## Gap 1: Persona Depth Model

### What MiroFish proved

MiroFish's `OasisAgentProfile` carries: MBTI type, age, gender, country, profession, activity-hour patterns, interest topics, and a long-form LLM-generated `persona` field ("highly detailed character"). These fields cause agents to produce meaningfully different behavior — an INTJ expert-level user navigates silently and efficiently; an anxious newcomer reads every tooltip and hesitates at ambiguous CTAs.

### Current state in LR

**`launch-rehearsal/src/rehearse/dsl.py:65-70`**
```python
@dataclass
class Persona:
    id: str
    name: str
    role: str
    goals: list[str]
    enabled: bool = True
```

**`launch-rehearsal/src/rehearse/persona_journey_discovery.py:24-31`** — the system prompt injected into every journey generation call:
```python
_PLAN_SYSTEM = """You are a {persona_role} who uses software products.
You deeply understand your own usage patterns..."""

_PLAN_PROMPT = """You are: {persona_name}
Your role: {persona_role}
Your goals: {persona_goals}
...
```

The LLM generating steps receives `name`, `role`, and `goals` — nothing about *how* this persona would behave in the presence of uncertainty, ambiguity, or friction. All personas navigate with similar "test engineer" precision regardless of who they're supposed to be.

### What's missing

| Attribute | Impact if missing |
|---|---|
| `tech_literacy` | Novice vs. expert would use completely different paths — novices search, experts navigate directly |
| `patience` | A low-patience persona should abandon a 3-step flow and look for shortcuts |
| `trust_level` | Skeptics read fine print; trusting users skip it — this changes what they notice |
| `character` | Free-text psychological texture: "anxious about billing surprises", "compares everything before committing" |
| `usage_context` | "First time using this category of product" vs. "switched from Competitor X" changes assumptions |

### Proposed schema addition

**`dsl.py`** — extend `Persona`:
```python
@dataclass
class Persona:
    id: str
    name: str
    role: str
    goals: list[str]
    enabled: bool = True
    # behavioral depth (all optional, safe defaults)
    tech_literacy: str = "intermediate"     # "novice" | "intermediate" | "expert"
    patience: str = "medium"                # "low" | "medium" | "high"
    trust_level: str = "neutral"            # "skeptical" | "neutral" | "trusting"
    character: str = ""                     # free-text: psychological texture
    usage_context: str = ""                 # "first-time user", "switching from X", etc.
```

**`persona_journey_discovery.py`** — inject into both `_PLAN_SYSTEM` and `_EXPAND_SYSTEM`:
```python
_PLAN_SYSTEM = """You are a {persona_role} who uses software products.
Tech literacy: {tech_literacy}. Patience level: {patience}. Trust disposition: {trust_level}.
{character}
Navigate as this specific person would — a novice hesitates and reads; an expert scans and acts.
A low-patience user abandons flows that require more than 2 steps to find something obvious."""
```

**`persona_journey_discovery.py`** — in `_discover_journey_plan()` and `_expand_journey_steps()`, add the new fields to the format call:
```python
system = _PLAN_SYSTEM.format(
    persona_role=persona.get("role", "user"),
    tech_literacy=persona.get("tech_literacy", "intermediate"),
    patience=persona.get("patience", "medium"),
    trust_level=persona.get("trust_level", "neutral"),
    character=persona.get("character", ""),
)
```

**Behavioral judge** — `llm.py` SYSTEM_PROMPT should also reference these fields when evaluating whether a step outcome is a blocker vs. expected friction for *this* persona type.

### Files to change

| File | Change |
|---|---|
| `launch-rehearsal/src/rehearse/dsl.py` | Add 5 optional fields to `Persona` dataclass |
| `launch-rehearsal/src/rehearse/dsl.py` | Update `_load_config()` to read new fields from YAML with defaults |
| `launch-rehearsal/src/rehearse/persona_journey_discovery.py` | Extend `_PLAN_SYSTEM`, `_EXPAND_SYSTEM` templates |
| `launch-rehearsal/src/rehearse/persona_journey_discovery.py` | Inject new fields in `_discover_journey_plan()` and `_expand_journey_steps()` |
| `launch-rehearsal/src/rehearse/llm.py` | Extend `SYSTEM_PROMPT` + `analyze_persona_llm()` evidence bundle to include behavioral fields |
| `Frontend_V1/src/components/persona-editor-panel.tsx` | Add UI fields for tech_literacy, patience, trust_level, character |
| `launch-rehearsal/artifacts/configs/argyle.yaml` | Update example config with new persona fields |
| `launch-rehearsal/artifacts/configs/lr-self.yaml` | Same |

### Effort estimate
**~1 day.** This is purely additive — no execution pipeline changes. The persona YAML format is backward-compatible (all new fields have defaults).

---

## Gap 2: Persistent Agent Memory Between Steps

### What MiroFish proved

MiroFish agents maintain a graph-based memory (via Zep) that persists across simulation rounds. When an agent sees something in round 3, it informs their decision in round 7. The key pattern is: **observe → store → retrieve → decide**, not a one-shot plan replayed blindly.

### Current state in LR

Journey execution in LR is a two-phase pipeline:

```
Phase 1 (journey_discovery.py): LLM generates ALL steps upfront as a static list
         → steps are YAML-like: {action, intent, url, value}

Phase 2 (browser.py / journey_agent.py): Playwright replays each step mechanically
         → execute_step() has no LLM involvement
         → each step has no knowledge of what prior steps actually rendered
```

**`journey_agent.py:55-74`** — the execution loop:
```python
for i, step in enumerate(journey.steps):
    snap = session.execute_step(
        step,
        step_id=step_id,
        journey_id=journey.id,
        journey_name=journey.name,
        persona_id=primary,
        viewport=viewport,
    )
```

`execute_step()` receives a pre-planned `Step` object and executes it. No observation from previous steps is fed back.

### Why this causes the "generic journey" problem

When the LLM generates steps in Phase 1, it has the interaction map (DOM reference) but not live browser state. So it invents labels like "click the analytics section link" instead of "click the 'Candidate Database' link" — because at generation time, it doesn't know what the browser will actually show at step 3.

With memory, step 3's generation would see: *"step 2 landed on /dashboard, page title is 'Faculty Dashboard', nav contains: Candidates, Schedule, Analytics, Settings"* — and generate a grounded step.

### Proposed architecture shift

**From pre-planned to adaptive step generation:**

```
Current:
  [generate_all_steps(persona, product)] → static list → [replay mechanically]

Proposed:
  for each step:
    [generate_next_step(persona, product, scratchpad)] 
    → [execute_step]
    → [observe: url, title, visible_elements, outcome]
    → [append observation to scratchpad]
    → repeat
```

The `scratchpad` is a `list[dict]` threaded through the journey execution loop. No Zep, no external service — just a growing list of observations injected into each LLM call.

### Observation schema per step

```python
{
  "step": 3,
  "action": "click",
  "intent": "Candidate Database",
  "outcome": "pass",
  "landed_url": "/candidates",
  "page_title": "Candidates | Faculty Dashboard",
  "visible_nav": ["Dashboard", "Candidates", "Schedule", "Analytics", "Settings"],
  "note": "Table showed 12 rows, Export button visible top-right"
}
```

### Files to change

| File | Change |
|---|---|
| `launch-rehearsal/src/rehearse/persona_journey_discovery.py` | Add `generate_next_step(journey_meta, persona, product, scratchpad)` function |
| `launch-rehearsal/src/rehearse/persona_journey_discovery.py` | New prompt template `_NEXT_STEP_SYSTEM` / `_NEXT_STEP_PROMPT` that includes scratchpad as context |
| `launch-rehearsal/src/rehearse/browser.py` | Add `observe_page_state(page) -> dict` helper that extracts: URL, title, nav labels, button labels, headings |
| `launch-rehearsal/src/rehearse/agents/journey_agent.py` | Rewrite execution loop: per-step generate → execute → observe → append |
| `launch-rehearsal/src/rehearse/agents/journey_agent.py` | Thread `scratchpad: list[dict]` through `_replay_journey_from_start()` |
| `launch-rehearsal/src/rehearse/dsl.py` | `Journey.steps` becomes optional — empty means adaptive generation at runtime |

### The new execution loop (journey_agent.py)

```python
scratchpad: list[dict] = []
max_steps = journey_meta.get("expected_steps", 12)

for i in range(max_steps):
    # Generate next step given what we've seen so far
    step = generate_next_step(
        journey_meta, persona_obj, product_model, scratchpad
    )
    if step is None or step.action == "done":
        break

    snap = session.execute_step(step, step_id=..., ...)
    
    # Observe and append to scratchpad
    observation = session.observe_page_state()
    observation.update({
        "step": i + 1,
        "action": step.action,
        "intent": step.intent,
        "outcome": snap.outcome,
        "note": snap.note,
    })
    scratchpad.append(observation)
    snaps.append(snap)
```

### Pre-planned journeys as a fallback

Hand-written YAML journeys (current behavior) should still work. The `Journey.steps` list being non-empty means "replay these exactly." Empty steps means "generate adaptively." This keeps backward compatibility with existing configs.

### Effort estimate
**~3–5 days.** This is a meaningful architecture change to the execution loop. The main risk is that adaptive generation may sometimes produce invalid steps (wrong selectors, non-existent URLs). A fallback to the current static path is essential until the adaptive loop is proven reliable.

### Cost consideration
Each adaptive step adds 1 LLM call. A 10-step journey → 10 calls instead of 1. At DeepSeek pricing (~$0.14/1M tokens), this is still cheap, but latency increases. Consider batching: generate 3 steps ahead at a time instead of 1.

---

## Implementation Roadmap

### Phase 1 — Persona Depth (do first, low risk)
- [ ] Extend `Persona` dataclass with 5 optional behavioral fields
- [ ] Update YAML loader to read new fields with safe defaults
- [ ] Extend `_PLAN_SYSTEM` + `_EXPAND_SYSTEM` prompt templates
- [ ] Update `discover_journeys_for_persona()` format calls
- [ ] Update behavioral judge prompt in `llm.py`
- [ ] Add fields to persona editor UI (`persona-editor-panel.tsx`)
- [ ] Update example configs (`argyle.yaml`, `lr-self.yaml`) with new persona fields
- [ ] Run a test with 3 personas (novice/expert/skeptical) to validate behavioral divergence

### Phase 2 — Adaptive Memory Loop (do after Phase 1 is validated)
- [ ] Add `observe_page_state(page) -> dict` to `browser.py`
- [ ] Write `generate_next_step()` + `_NEXT_STEP_PROMPT` in `persona_journey_discovery.py`
- [ ] Rewrite execution loop in `journey_agent.py` to use scratchpad
- [ ] Make `Journey.steps` optional (empty = adaptive)
- [ ] Implement fallback: if `generate_next_step()` returns invalid step 3x, fall back to template steps
- [ ] Add scratchpad dump to `StepSnapshot` for debugging and evidence
- [ ] Test against Argyle Faculty Dashboard — compare journey quality before/after
- [ ] Gate behind a config flag (`adaptive_steps: true`) until stable

### Phase 3 — Cross-Journey Memory (future, only if Phase 2 validates)
- [ ] Persist scratchpad from Journey A into context for Journey B of the same persona
- [ ] Structure as a "product mental model" dict: pages seen, features found, friction encountered
- [ ] Inject into journey generation to prevent redundant exploration

---

## Risks and Tradeoffs

| Risk | Mitigation |
|---|---|
| Adaptive generation produces invalid selectors | Step-level retry + fallback to template |
| LLM call count increases 10x for adaptive mode | Batch: generate 3 steps at a time; gate behind flag |
| Persona depth fields add YAML verbosity | All fields optional; defaults maintain current behavior |
| Stochastic adaptive steps reduce run reproducibility | Log every generated step to evidence bundle; scratchpad in artifacts |
| Behavioral divergence between personas is subtle, not dramatic | Test explicitly: run same journey with novice vs. expert, check step count and path differences |

---

## What this is NOT

- We are **not** integrating MiroFish's code, OASIS, or Zep into LR
- We are **not** adding social simulation or emergent cohort analysis (that's a V3 idea)
- We are **not** changing LR's output format (scorecards, screenshots, evidence bundles stay the same)

These are targeted improvements to input quality (persona richness) and execution quality (observation-grounded step generation). The scorecard a PM sees on Thursday before launch should look exactly the same — just with more credible, differentiated, realistic behavior driving it.
