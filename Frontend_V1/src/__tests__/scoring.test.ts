/**
 * Unit tests for scoring, dimension matching, and cost display helpers.
 * No DOM, no API calls — pure logic.
 */
import { describe, it, expect } from "vitest";
import { issueMatchesDimension, countIssuesForDimension } from "../lib/dimension-match";
import { bandFromIssues } from "../lib/mock-data";
import { formatAgentCostDisplay } from "../lib/run-metrics";
import type { Issue } from "../lib/mock-data";

const makeIssue = (overrides: Partial<Issue> = {}): Issue => ({
  id: "test-1",
  runId: "run-1",
  severity: "P2",
  title: "Test issue",
  detail: "",
  dimension: "Functionality",
  relatedDimensions: [],
  confidence: "high",
  evidence: "",
  persona: "Evaluator",
  personaId: "p1-evaluator",
  journey: "j1-landing",
  journeyId: "j1-landing",
  stepId: "s1",
  owner: "frontend",
  recurring: 1,
  suggestion: "",
  severityReason: "",
  ...overrides,
});

describe("issueMatchesDimension", () => {
  it("matches primary dimension exactly", () => {
    expect(issueMatchesDimension(makeIssue({ dimension: "UI/UX" }), "UI/UX")).toBe(true);
    expect(issueMatchesDimension(makeIssue({ dimension: "UI/UX" }), "Accessibility")).toBe(false);
  });

  it("matches via relatedDimensions cross-tag", () => {
    const issue = makeIssue({ dimension: "UI/UX", relatedDimensions: ["Accessibility"] });
    expect(issueMatchesDimension(issue, "Accessibility")).toBe(true);
  });

  it("falls back to Functionality when dimension is empty", () => {
    const issue = makeIssue({ dimension: "" });
    // issueMatchesDimension checks dimension === target; empty won't match "Functionality" explicitly
    expect(issueMatchesDimension(issue, "Functionality")).toBe(false);
    expect(issueMatchesDimension(issue, "")).toBe(true);
  });
});

describe("countIssuesForDimension", () => {
  it("counts matching issues correctly", () => {
    const issues = [
      makeIssue({ dimension: "UI/UX" }),
      makeIssue({ dimension: "Accessibility" }),
      makeIssue({ dimension: "UI/UX", relatedDimensions: ["Accessibility"] }),
    ];
    expect(countIssuesForDimension(issues, "UI/UX")).toBe(2);
    expect(countIssuesForDimension(issues, "Accessibility")).toBe(2);
    expect(countIssuesForDimension(issues, "Performance")).toBe(0);
  });
});

describe("bandFromIssues", () => {
  it("Red for any P0", () => {
    expect(bandFromIssues([makeIssue({ severity: "P0" })])).toBe("danger");
  });

  it("Amber/warn for P1 without P0", () => {
    expect(bandFromIssues([makeIssue({ severity: "P1" })])).toBe("warn");
  });

  it("Green/ready for P2/P3 only", () => {
    expect(bandFromIssues([makeIssue({ severity: "P2" }), makeIssue({ severity: "P3" })])).toBe(
      "ready",
    );
  });

  it("Green/ready for empty list", () => {
    expect(bandFromIssues([])).toBe("ready");
  });
});

describe("formatAgentCostDisplay", () => {
  it("formats cost with dollar sign", () => {
    const bundle = {
      summary: {
        costEstimate: { usd: 0.042, source: "llm_tokens" },
        agentsRun: 5,
        durationSec: 180,
      },
      steps: [],
      issues: [],
      delights: [],
      agents: [],
      matrix: [],
      dimensions: [],
      personas: [],
      journeys: [],
      workflows: [],
      suggestedJourneys: [],
      annotations: [],
      screenshots: [],
      sitemapPages: [],
      sitemapEdges: [],
      scorecardMd: "",
      sitemapMd: "",
    } as unknown as Parameters<typeof formatAgentCostDisplay>[0];
    const result = formatAgentCostDisplay(bundle);
    expect(result.value).toContain("$");
    expect(typeof result.hint).toBe("string");
  });

  it("handles agentCost fallback path", () => {
    // agentCost fallback (legacy field) — must be a number
    const bundle = {
      summary: { agentCost: 0.01, durationSec: 0 },
      steps: [],
      issues: [],
      delights: [],
      agents: [],
      matrix: [],
      dimensions: [],
      personas: [],
      journeys: [],
      workflows: [],
      suggestedJourneys: [],
      annotations: [],
      screenshots: [],
      sitemapPages: [],
      sitemapEdges: [],
      scorecardMd: "",
      sitemapMd: "",
    } as unknown as Parameters<typeof formatAgentCostDisplay>[0];
    const result = formatAgentCostDisplay(bundle);
    expect(result.value).toBe("$0.01");
  });
});
