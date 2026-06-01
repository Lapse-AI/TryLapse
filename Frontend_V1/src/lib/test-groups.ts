/** Dev-only rehearsal personas — maps UI test groups to target URLs and YAML configs. */

export type TestGroupId = "cal-com" | "argyle" | "lr-self" | "staging";

export interface TestGroup {
  id: TestGroupId;
  label: string;
  personaLabel: string;
  description: string;
  targetUrl: string;
  /** Preferred config id (example or saved artifact stem). */
  configId: string;
  /** Match newest saved config when exact id is missing (e.g. argyle-*). */
  configIdPrefixes?: string[];
  productName?: string;
  withAuth?: boolean;
  selfTest?: boolean;
  allowLocalhost?: boolean;
}

export const TEST_GROUPS: TestGroup[] = [
  {
    id: "cal-com",
    label: "Cal.com",
    personaLabel: "Cal.com marketing tester",
    description: "Public SaaS surface — pricing, signup, product depth",
    targetUrl: "https://cal.com",
    configId: "cal-com-phase0",
    productName: "Cal.com (practice target)",
  },
  {
    id: "argyle",
    label: "Argyle dashboard",
    personaLabel: "Argyle faculty dashboard tester",
    description: "Authenticated faculty dashboard — REHEARSE_EMAIL / REHEARSE_PASSWORD",
    targetUrl: "https://faculty-dashboard-eight.vercel.app",
    configId: "argyle-20260531-000517",
    configIdPrefixes: ["argyle"],
    productName: "Argyle Faculty Dashboard",
    withAuth: true,
  },
  {
    id: "lr-self",
    label: "Self-test (this UI)",
    personaLabel: "Launch Rehearsal self-test tester",
    description: "Dogfood this dashboard at localhost:8081",
    targetUrl: "http://127.0.0.1:8081",
    configId: "lr-self",
    configIdPrefixes: ["lr-self", "self-dashboard"],
    productName: "Launch Rehearsal Dashboard",
    selfTest: true,
    allowLocalhost: true,
  },
  {
    id: "staging",
    label: "Staging (generic)",
    personaLabel: "Enterprise staging tester",
    description: "Generic authenticated SaaS template — swap target in Init",
    targetUrl: "https://example.com",
    configId: "enterprise-saas",
    productName: "Example Enterprise SaaS",
    withAuth: true,
  },
];

export const DEFAULT_TEST_GROUP_ID: TestGroupId = "lr-self";

export function getTestGroup(id: string | null | undefined): TestGroup {
  return (
    TEST_GROUPS.find((g) => g.id === id) ?? TEST_GROUPS.find((g) => g.id === DEFAULT_TEST_GROUP_ID)!
  );
}

export function resolveGroupConfigId(group: TestGroup, configs: Array<{ id: string }>): string {
  if (configs.some((c) => c.id === group.configId)) return group.configId;
  for (const prefix of group.configIdPrefixes ?? []) {
    const match = configs.find((c) => c.id === prefix || c.id.startsWith(`${prefix}-`));
    if (match) return match.id;
  }
  return group.configId;
}

export type TestGroupInitPreset = Pick<
  TestGroup,
  "targetUrl" | "productName" | "withAuth" | "selfTest" | "allowLocalhost"
>;

export function groupInitPreset(group: TestGroup): TestGroupInitPreset {
  return {
    targetUrl: group.targetUrl,
    productName: group.productName,
    withAuth: group.withAuth ?? false,
    selfTest: group.selfTest ?? false,
    allowLocalhost: group.allowLocalhost ?? group.selfTest ?? false,
  };
}

/** Match a run to a product test group (run id prefix, target host, product name). */
export function runMatchesTestGroup(
  run: { id: string; targetUrl?: string; productName?: string },
  group: TestGroup,
): boolean {
  const prefixes = [group.configId, ...(group.configIdPrefixes ?? [])];
  const idLower = run.id.toLowerCase();
  if (prefixes.some((p) => idLower === p || idLower.startsWith(`${p}-`))) return true;

  if (run.targetUrl) {
    try {
      const runHost = new URL(run.targetUrl).hostname.replace(/^www\./, "");
      const groupHost = new URL(group.targetUrl).hostname.replace(/^www\./, "");
      if (runHost === groupHost) return true;
      if (group.selfTest && (runHost === "127.0.0.1" || runHost === "localhost")) return true;
    } catch {
      /* ignore */
    }
  }

  if (run.productName && group.productName) {
    const a = run.productName.toLowerCase();
    const b = group.productName.toLowerCase();
    if (a.includes(b.slice(0, 12)) || b.includes(a.slice(0, 12))) return true;
  }

  if (group.id === "staging") {
    return idLower.startsWith("enterprise-");
  }

  return false;
}

/** Match a background job to a product test group via its config path. */
export function jobMatchesTestGroup(job: { config?: string }, group: TestGroup): boolean {
  const path = job.config ?? "";
  if (!path) return false;
  const stem = path.replace(/\\/g, "/").split("/").pop()?.replace(/\.yaml$/, "") ?? "";
  if (stem === group.configId) return true;
  for (const prefix of group.configIdPrefixes ?? []) {
    if (stem === prefix || stem.startsWith(`${prefix}-`)) return true;
  }
  if (group.id === "staging" && stem.startsWith("enterprise-")) return true;
  return false;
}
