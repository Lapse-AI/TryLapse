# Scoring Trust Mechanisms: How Automated Readiness Scores Earn Engineering Team Trust
*Deep Research | Generated: 2026-06-16 | Method: Web research + domain synthesis*

---

## Table of Contents
1. [Lighthouse Performance Score](#lighthouse)
2. [Core Web Vitals (CWV)](#cwv)
3. [WCAG and Axe Accessibility Scoring](#wcag)
4. [CVSS Security Scoring](#cvss)
5. [SonarQube Quality Gates](#sonarqube)
6. [Datadog SLOs and Error Budgets](#datadog)
7. [Google SRE Production Readiness Review](#sre)
8. [AWS Well-Architected Framework](#aws)
9. [Statistical Calibration Theory](#calibration)
10. [Psychometrics and Composite Scoring](#psychometrics)
11. [NPS Trust Mechanics](#nps)
12. [Engineering Team Metric Adoption Psychology](#adoption)
13. [**Synthesis: What Launch Rehearsal Must Build**](#synthesis)

---

## 1. Lighthouse Performance Score {#lighthouse}

**Score type:** 0–100 numeric composite

**How the score is built:**
Weighted average of six metrics: First Contentful Paint (10%), Speed Index (10%), Largest Contentful Paint (25%), Total Blocking Time (30%), Cumulative Layout Shift (25%). Each metric converts to a 0–100 subscale using log-normal curves derived from real-world HTTPArchive data, then the weighted composite is computed.

**Why it builds trust:**

*Transparency:* Full methodology is open-source and documented on GitHub (`lighthouse/docs/scoring.md`). The scoring calculator is public — you can see exactly why your score is 72 vs. 80. Nothing is hidden.

*Signal grounding:* Every metric maps to a moment a human would feel: "when did I see something?" (FCP), "when could I click?" (TBT), "did things jump around?" (CLS). Engineers can feel these — they're not abstract.

*Benchmarkable:* Same tool, same methodology, any site. Industry comparisons are possible: "our score is 72, industry median for B2B SaaS is 65."

*Threshold anchoring:* 0–49 = Red, 50–89 = Orange, 90–100 = Green. Clear bands mean "we need to get above 90" is a meeting-friendly target.

*SEO leverage:* Google's Core Web Vitals are a ranking signal. This extrinsic pressure means engineering managers *must* care about the score, not just developers.

**Common failure modes:**
- Lighthouse is a lab metric (simulated throttling, cold cache) — real user experience can differ significantly
- Scores are sensitive to timing and resource order — same page can score differently on consecutive runs
- Engineers learn to optimize for the score (compression, defer loading) without improving actual UX

**Lessons for Launch Rehearsal:**
1. **Publish the scoring methodology openly** — "here is exactly how we compute each of the 8 dimensions" reduces the "is this made up?" objection
2. **Map every metric to something a human can feel** — "UI/UX score is 62 because 7 buttons had no accessible label" is citable; "UI/UX score is 62 because our AI said so" is not
3. **Provide a scoring calculator or score breakdown** — let teams trace the exact signals that produced each dimension score
4. **Use color bands, not just numbers** — Red/Amber/Green is already in the codebase; preserve it

---

## 2. Core Web Vitals {#cwv}

**Score type:** Three categorical ratings (Good/Needs Improvement/Poor per metric), aggregate pass/fail

**How thresholds are set:**
Google defined each threshold empirically: "what value at the 75th percentile of real Chrome user sessions gives a good experience, based on user research and field data?" P75 was chosen because it's representative of most users without being dominated by extreme outliers. A page "passes" CWV only when all three metrics (LCP, INP, CLS) clear their Good threshold at the 75th percentile of real user sessions over a rolling 28-day window.

**Why it builds trust:**

*External authority:* Google owns it. That alone gives it the "I can cite this in any meeting" property. Engineering managers don't need to understand why LCP ≤ 2.5s is the threshold — Google said so.

*Field data, not lab data:* CWV uses real Chrome user sessions (CrUX dataset). This gives it "this is what your actual users experience" credibility — not a simulated proxy.

*Named thresholds with empirical backing:* "Good" threshold is not arbitrary — it's derived from user research showing perceptible quality difference. The web.dev article "How Core Web Vitals Thresholds Were Defined" is publicly available. The rationale is documented.

*Industry adoption creates reference points:* When competitors' CWV scores are public (via PageSpeed Insights), comparisons become possible. "Our LCP is 1.8s, competitor is 3.2s" is a business argument.

**Lessons for Launch Rehearsal:**
1. **Anchor thresholds to observable outcomes, not arbitrary numbers** — "Onboarding score < 60 correlates with auth failure or no onboarding paths found" is more credible than "< 60 means bad"
2. **Use rolling window logic for recurrence tracking** — CWV's 28-day rolling window is a trust mechanism: it's not one bad run, it's a pattern. Launch Rehearsal's cross-run recurrence tracking is already doing this
3. **Show the percentile, not just the number** — "your Functionality score is 72 (top 40% of runs we've seen)" adds benchmarking context that a standalone 72 lacks

---

## 3. WCAG and Axe Accessibility Scoring {#wcag}

**Score type:** Categorical (Level A, AA, AAA conformance) + automated issue counts per severity

**How thresholds are set:**
WCAG criteria are normative and maintained by W3C. Each criterion is binary: pass or fail. Axe converts this to issue severity (critical, serious, moderate, minor) based on user impact research.

**Why it builds trust:**

*Regulatory anchoring:* WCAG 2.1 AA is legally required in many contexts (ADA in the US, EN 301 549 in the EU). External legal compulsion removes the "optional" perception that kills adoption of voluntary metrics.

*Binary at the criterion level:* Each WCAG criterion is pass/fail, not "mostly ok." This forces accountability — you can't score 78/100 on "images have alt text." Either they do or they don't.

*Axe's 3% false-positive rate:* Deque Labs (who maintain Axe) specifically focus on eliminating false positives. Engineering teams will use a tool they can trust not to cry wolf.

**Lessons for Launch Rehearsal:**
1. **Binary outcomes for binary questions** — "auth succeeded: yes/no" shouldn't be a 0-100 scale; it should be a blocker flag
2. **The false-positive rate is a trust signal** — if Launch Rehearsal raises issues that aren't actually real problems, teams will learn to ignore all issues. Precision matters more than recall for trust
3. **Separate "regulatory" from "quality"** — Accessibility and Trust dimensions map to external standards teams must care about; frame them differently from opinion-based dimensions

---

## 4. CVSS Security Scoring {#cvss}

**Score type:** 0.0–10.0 numeric, mapped to bands (None/Low/Medium/High/Critical)

**How it's built:**
Three component scores: Base (inherent properties of the vulnerability), Temporal (exploitability signals that change over time), Environmental (organization-specific impact adjustments). Published as both a vector string (transparent, reproducible) and a numeric score (actionable).

**Why it builds trust:**

*Cross-vendor consistency:* NVD, Tenable, Qualys, Wiz, Rapid7 — every security vendor uses CVSS as the reference. When everyone uses the same score, it becomes a lingua franca you can cite to any audience.

*Published by FIRST (neutral body):* CVSS is not a vendor metric — it's maintained by a neutral international standards body. Neutrality = credibility.

*Vector string transparency:* Behind every CVSS score is a vector string like `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`. Any practitioner can decode it. The score isn't magic — it's a formula applied to documented inputs.

*Severity band language:* "Critical" means something specific — don't dismiss it. "Low" means something specific — it's OK to defer it. The bands reduce decision fatigue.

**Lessons for Launch Rehearsal:**
1. **P0/P1/P2/P3 severity bands already exist** — this is right. CVSS-style severity is one of the most trusted patterns in engineering. Keep it.
2. **Severity must be reproducible** — if the same issue produces P1 in one run and P2 in another without any change, trust collapses. Severity logic must be deterministic.
3. **Publish the severity logic as a matrix** — "P1 if: auth failure, budget exceeded, BrowserStepTimeout; P2 if: unlabeled UI, CLS issue; P3 if: performance, thin content" — a published matrix is more trustworthy than a black box

---

## 5. SonarQube Quality Gates {#sonarqube}

**Score type:** Binary gate (Pass/Fail) on a named policy, backed by multiple sub-metrics

**How it works:**
A quality gate is a named set of conditions (e.g., "no new critical bugs, coverage on new code ≥ 80%, no new security hotspots"). The gate status is a hard binary — it either passes or fails. Individual metrics are visible but the gate output is actionable: block or allow.

**Why it builds trust:**

*Binary output = clear action* — "Quality Gate: FAILED" in the CI pipeline is unambiguous. "Score: 67/100" requires interpretation. Binary gates eliminate the cognitive cost of deciding whether to act.

*"New code" focus prevents frustration* — SonarQube's default "Sonar Way" gate applies only to new code introduced in the current PR. This prevents the paralysis of "we have 2,000 legacy issues" blocking all new work.

*Low false-positive rate (< 3% claimed)* — engineering teams trust the gate because it doesn't cry wolf on every commit.

*Opt-in discipline* — quality gates work because engineering orgs decide their thresholds. The gate is a commitment they made to themselves, not an external judgement.

**Lessons for Launch Rehearsal:**
1. **Add a "Launch Gate" concept** — a named pass/fail verdict above the readiness score: "Launch Gate: PASS (score 82, no P0 blockers)" vs. "Launch Gate: BLOCKED (P0 auth failure found)." This is the single most impactful addition for meeting-room citation.
2. **Focus on delta, not absolute** — "2 new issues since last run" is more actionable than "12 total issues"
3. **Let teams set their own thresholds** — "we won't ship below 70 Functionality" = their commitment, not Launch Rehearsal's judgment. This increases ownership.

---

## 6. Datadog SLOs and Error Budgets {#datadog}

**Score type:** Percentage (99.9%), time-windowed, mapped to error budget burn rate

**How it works:**
Service Level Objectives define an uptime or latency target over a rolling window. The "error budget" is the allowed failure rate. Teams track burn rate — are you consuming the error budget faster than allowed? This signals risk before the SLO is breached.

**Why it builds trust:**

*Longitudinal by design* — SLO trust comes from the time window: "we've been at 99.97% for 30 days" is more credible than a single measurement. Cross-run recurrence tracking is exactly this principle.

*Business language* — "we've burned 80% of our error budget this week" translates into "we are at risk of breaching our SLA and owing customers credits." The score connects to consequences.

*Alert on burn rate, not breach* — sophisticated users track burn rate acceleration, not just whether the SLO is currently passing. This is forward-looking signal.

**Lessons for Launch Rehearsal:**
1. **Cross-run recurrence tracking is the right moat** — already implemented. "This issue has appeared in 4 of the last 6 runs" is Datadog SLO logic applied to behavioral testing. It's forward-looking and sticky.
2. **Show trend lines, not snapshots** — a readiness score that shows "72 → 68 → 64 over 3 runs" is an alert signal. A standalone 64 is just a number.
3. **Error budget concept for launch decisions** — "you have 2 P0-equivalent issues remaining in your launch budget this sprint" is a meeting-ready statement

---

## 7. Google SRE Production Readiness Review {#sre}

**Score type:** Checklist-based, not numeric — named criteria, stakeholder sign-off, "ready / not ready"

**How it works:**
The PRR is a structured questionnaire covering: service levels, architecture, performance, documentation, observability, testing, deployment strategy. Each dimension has specific questions. The output is a list of gaps + a decision: onboard to SRE or not.

**Why it builds trust:**

*Named criteria, not a number* — "your observability is incomplete (no runbook for the auth failure case)" is more actionable than "your readiness is 72." Named gaps create named owners.

*Stakeholder sign-off* — the PRR requires multiple stakeholders (dev team, SRE team) to sign off. The process creates organizational commitment, not just individual awareness.

*Proportional to risk* — the PRR depth scales with the risk profile of the service. A trivial internal tool gets a light PRR; a customer-facing revenue service gets a full PRR. Proportionality prevents fatigue.

*Ongoing, not one-time* — PRR isn't done at launch and forgotten. It's revisited at major milestones. This creates the habit loop that makes SRE relationships sticky.

**Lessons for Launch Rehearsal:**
1. **Add named gap descriptions to every issue** — "Onboarding dimension failed because: no `/signup` or `/register` paths found in the crawl, and auth returned error code on first journey" is a named gap. "Onboarding: 45" is not.
2. **Stakeholder mode** — design a view for "PM/launch lead" vs "developer" — same data, different presentation. PMs need a launch decision; developers need debugging info. Both must be able to cite the report in their respective contexts.
3. **Proportion the depth** — a first-time scan of a new product should have a "light" report (top 5 findings); a 10th run of a mature product should have a "deep" report (trend analysis, recurrence map, regression detection).

---

## 8. AWS Well-Architected Framework {#aws}

**Score type:** Named pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability) + question-level pass/warn/fail

**Why it builds trust:**

*Pillar-based structure* — "your Security pillar has 3 high-risk findings" is citable at the VP level without requiring technical depth. Pillar names translate into org chart language.

*Question-level specificity* — each pillar has 20-40 specific questions. A "high risk" finding maps to a specific question that maps to a specific practice. Traceability from score → dimension → specific finding → remediation step.

*AWS-backed authority* — same as Google/WCAG: external authority removes the "is this just someone's opinion?" objection.

*Partner ecosystem* — AWS Well-Architected Reviews are performed by AWS Partners; the framework is currency in enterprise conversations.

**Lessons for Launch Rehearsal:**
1. **Dimension names should be board-room safe** — Functionality, UI/UX, Information Clarity, Performance, Accessibility, Trust, Onboarding, Recovery — these names already pass the VP-level test. Keep them.
2. **Build a "scorecard" view** — one-page: 8 dimensions with scores + top finding per dimension. This is the AWS WAR review output equivalent. This is what a PM prints and brings to a launch decision meeting.
3. **"High-risk finding" language** — adoption of "high risk" and "medium risk" alongside P0-P3 severity gives the report dual-register communication (technical and business).

---

## 9. Statistical Calibration Theory {#calibration}

**The core concept:**
A score is "well-calibrated" if events labeled with confidence X% actually occur X% of the time. A reliability diagram plots predicted confidence vs. actual frequency — a perfectly calibrated model produces a diagonal line. Overconfident models show actual frequency below predicted confidence; underconfident models show the reverse.

**Why calibration matters for user trust:**
Research on miscalibrated AI confidence shows: users are sensitive to confidence scores and use them when deciding whether to act on a prediction. Overconfident scores ("Score: 94/100 — Ready to ship!") that precede failures destroy trust permanently. Underconfident scores ("Score: 58/100") on a good product cause false alarm fatigue.

**Practical calibration techniques:**
- *Platt scaling* — fit a logistic regression on top of model outputs to align predicted probabilities to empirical frequencies
- *Temperature scaling* — divide logit outputs by a learned temperature to calibrate confidence
- *Reliability diagrams* — visualize calibration; if "scores 70-80 correlate with 72% successful launches in your data," that's calibration evidence

**Lessons for Launch Rehearsal:**
1. **The most critical long-term trust work: calibrate the score against launch outcomes.** If you can show that "products scoring 80+ had 92% successful launches while products scoring below 60 had 67% of launches result in critical user complaints within 48 hours," the score becomes a real predictive instrument, not an opinion.
2. **Publish calibration data transparently.** "Based on 150 run-to-launch pairs, our readiness score predicts launch success with 78% accuracy at the 70+ threshold." This is the single most powerful trust-building statement you can make.
3. **Be honest about calibration gaps in early days.** "We do not yet have enough data to calibrate our Accessibility dimension against real outcomes; treat this as directional, not predictive." Honest uncertainty is more trustworthy than false precision.
4. **Avoid overconfidence bands.** Don't let the score say "launch-ready" until you have calibration data that justifies it. Use language like "no blocking issues found" rather than "ready to ship."

---

## 10. Psychometrics and Composite Scoring {#psychometrics}

**The core concept:**
Academic psychometrics (IRT, Rasch models, factor analysis) studies how to construct valid composite scores from multiple indicators. Key concepts:
- *Face validity:* does the score look like it's measuring what it claims to? Engineers must perceive it as measuring real behavioral quality, not arbitrary signals.
- *Construct validity:* do the sub-scores actually load onto the right theoretical constructs? Do all "UI/UX" signals actually correlate with each other?
- *Differential item functioning:* do some score items systematically disadvantage certain product types (e.g., SPAs being underscored on "Information Clarity" because of different DOM structure)?

**Why dimension weighting is a trust question:**
A composite that weights Functionality at 40% and Accessibility at 5% makes a statement about relative importance. If that weighting doesn't match the engineering team's values, they'll dismiss the overall score. Customizable weights (or transparent defaults) address this.

**Lessons for Launch Rehearsal:**
1. **Publish dimension weights** — "the overall readiness score is: 40% Functionality, 20% UI/UX, 15% Information Clarity, 10% Performance, 5% Accessibility, 5% Trust, 3% Onboarding, 2% Recovery." Or let teams set weights for their product priorities.
2. **Document what each dimension measures at the signal level** — "UI/UX dimension is computed from: unlabeled button count, average step duration, CLS-equivalent layout shift during navigation, input label coverage." Not "AI evaluates your UI."
3. **Watch for SPA / framework bias** — React SPAs have different crawl/DOM characteristics than server-rendered apps. If SPAs systematically score lower on Information Clarity because of hydration timing, that's a calibration problem that destroys trust with a specific customer segment.

---

## 11. NPS Trust Mechanics {#nps}

**Why NPS became universal despite methodological criticism:**

NPS is not the most statistically sophisticated metric. Academic critics note its failure to capture nuanced sentiment and susceptibility to cultural response bias. Yet it became the most widely adopted customer experience metric in the world. Why?

1. **One question** — you can collect it anywhere, in any context, with any team. Simplicity reduces friction to data collection.
2. **Executive-accessible language** — "47 NPS" requires no statistical literacy. CEOs, investors, and board members can react to it.
3. **Benchmarkable across companies** — "industry NPS for B2B SaaS is 30; ours is 47" is a competitive statement.
4. **Bain & Company's authority** — NPS was published in Harvard Business Review by Bain, backed by revenue correlation data. The external authority made it "safe to cite."
5. **Connects to money** — the NPS paper showed correlation with revenue growth. Business metrics that connect to money get organizational buy-in that purely technical metrics don't.

**Lessons for Launch Rehearsal:**
1. **Simplify the summary metric** — the 8-dimension breakdown is necessary for debugging, but the executive summary should be one number with a band. "Readiness: 74 (Amber)" — one glance, one decision.
2. **Connect the score to shipping outcomes** — when calibration data becomes available, the connection to "products at this score had 83% successful launches" is the equivalent of NPS's revenue correlation paper.
3. **Benchmarkability against industry peers** — "your readiness score is 74 vs. B2B SaaS median of 68" is a business statement. Build this aggregate benchmarking as the moat.

---

## 12. Engineering Team Metric Adoption Psychology {#adoption}

**Why engineers adopt some metrics and ignore others:**

Research and practitioner experience consistently shows:

*Actionability is the primary driver.* Teams cite and use metrics that produce a clear next action. "TBT is 1,200ms because of this blocking script" → fix the script. "Score: 67" → unclear what to do. Every score must produce a ranked list of actionable items or it won't be cited.

*Perceived fairness and legitimacy.* Metrics imposed from above are resisted; metrics derived from observable evidence are accepted. Teams that understand *why* a score is what it is will defend it to stakeholders. Teams that don't understand it will route around it.

*Goodhart's Law.* Every metric gets gamed by intelligent engineers. The only protection is making the underlying signals hard to fake (real user behavior simulation is harder to Goodhart than synthetic test scripts).

*Psychological safety.* Metrics used for punishment → gaming and hiding. Metrics used for improvement → honest tracking. The narrative around the readiness score matters as much as the score itself.

*Ritual integration beats dashboard availability.* Metrics that become part of team rituals (sprint retrospectives, launch checklists, PR review templates) get used. Metrics that live in a dashboard the team checks "when they remember" get ignored.

**What makes a score "citable" in a meeting:**
- It has a name that fits in a sentence ("our staging readiness score")
- It has a number that's memorable (74 is memorable; 0.748 is not)
- It has a clear interpretation direction ("higher is better")
- It has a band that translates to action ("Amber means we should fix the P0 before launch")
- It has a recent timestamp ("as of this morning")
- It has a benchmark ("vs. last sprint's 68")

**Lessons for Launch Rehearsal:**
1. **Every report must end with a ranked "Fix These First" list** — max 3-5 items, concrete, specific, owner-taggable. If the report doesn't suggest action, it won't be cited.
2. **Design for the sprint retro** — "our readiness score went from 68 to 74 this sprint" is a retro achievement. Design the score trend view with this framing in mind.
3. **Make it screenshot-able** — the one-page scorecard view (8 dimensions, overall score, top issues) should fit in a Slack message or Confluence page screenshot. If it takes effort to share, teams won't share it.
4. **Name the dimensions consistently** — "Functionality" must always mean the same thing. Score volatility (same product, same code, very different scores) is the fastest trust-killer.

---

## 13. Synthesis: What Launch Rehearsal Must Build {#synthesis}

### The Three Trust Levers

**Lever 1: Transparency (Lighthouse model)**
- Publish the full scoring methodology openly
- Show the exact signals behind each dimension score ("UI/UX: 62 because 7 unlabeled buttons, avg step duration 4.2s in journey X")
- Make scores reproducible: same URL, same config, very similar score ± some variance from real browser behavior
- Provide a scoring breakdown tool

**Lever 2: External Anchoring (CWV/WCAG model)**
- Build industry benchmarks by product type: "B2B SaaS sign-up flow median Onboarding score: 68"
- Publish calibration data as it accrues: "products scoring 80+ had X% fewer critical launch incidents in our data"
- Eventually: reference WCAG for Accessibility dimension, Core Web Vitals for Performance — piggybacking on established external authority

**Lever 3: Actionability (SonarQube model)**
- The "Launch Gate" concept: a named pass/fail verdict above the score
- Every issue has a concrete owner, suggested fix, severity reason, and screenshot
- Delta-first: "2 new issues since last run" before "12 total issues"
- Cross-run recurrence: "recurring ×3 runs" is an alert, not just information

### The Anti-Patterns to Avoid

1. **"AI says your app is ready"** — never. Lead with behavioral evidence (screenshots, step traces, journey matrix).
2. **Score volatility** — if the same product scores 74 and 51 on consecutive runs with no code change, trust collapses. Invest in score stability before adding dimensions.
3. **Overconfidence bands** — don't say "launch-ready" until you have calibration data. Say "no P0 blockers found."
4. **No action from score** — a readiness score with no actionable issues list is decoration.
5. **Complex scoring model** — if an engineer can't explain in 2 sentences why the score is what it is, they won't cite it.

### Priority Roadmap for Scoring Trust

| Priority | Initiative | Trust Lever |
|---|---|---|
| Now | Publish scoring methodology docs | Transparency |
| Now | Show exact signals per dimension in UI | Transparency |
| Now | "Launch Gate" pass/fail verdict | Actionability |
| Soon | Score trend view across runs | SLO/Datadog model |
| Soon | "Fix These First" ranked issue list (max 5) | Actionability |
| Q3 2026 | Industry median benchmarks by category | External anchoring |
| Q4 2026 | Calibration report: score vs. launch outcomes | Statistical calibration |
| 2027 | Publish calibration data as trust proof | NPS-equivalent external authority |

---

*Sources:*
- [Lighthouse scoring methodology](https://github.com/GoogleChrome/lighthouse/blob/main/docs/scoring.md)
- [How Core Web Vitals Thresholds Were Defined](https://web.dev/articles/defining-core-web-vitals-thresholds)
- [Understanding the Effects of Miscalibrated AI Confidence on User Trust](https://arxiv.org/html/2402.07632v4)
- [SonarQube Quality Gates documentation](https://docs.sonarsource.com/sonarqube-cloud/standards/managing-quality-gates/introduction-to-quality-gates)
- [Google SRE Production Readiness Review](https://sre.google/sre-book/evolving-sre-engagement-model/)
- [NPS: Net Promoter Score and UX](https://www.nngroup.com/articles/nps-ux/)
- [The engineering metrics used by top dev teams](https://getdx.com/blog/engineering-metrics-top-teams/)
- [Model calibration explained](https://towardsdatascience.com/model-calibration-explained-a-visual-guide-with-code-examples-for-beginners-55f368bafe72/)
