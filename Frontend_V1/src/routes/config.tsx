import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { personas, workspace, agentConfigDefaults, auditLog } from "@/lib/mock-data";
import { useWorkspace, useSaveWorkspace } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";

export const Route = createFileRoute("/config")({
  head: () => ({ meta: [{ title: "Workspace — Launch Rehearsal" }] }),
  component: Config,
});

const yaml = `# rehearse.yaml — matches launch-rehearsal/examples/enterprise-saas.yaml shape
product_name: Acme SaaS
target_url: https://app.acme.io
run_id_prefix: acme

crawl:
  enabled: true
  max_depth: ${agentConfigDefaults.crawlMaxDepth}
  max_pages: ${agentConfigDefaults.crawlMaxPages}
  respect_robots: ${agentConfigDefaults.crawlRespectRobots}

personas:
  - id: p1-evaluator
    name: Prospect Priya
    role: First-time visitor evaluating
    goals: [Decide if worth a demo]
  - id: p2-operator
    name: Operator Owen
    role: Daily power user
  - id: p3-admin
    name: Admin Ada
    role: Owns the workspace

journeys:
  - id: j1
    name: Land → Pricing → Signup
    steps:
      - action: navigate
        url: /
      - action: click
        selector: "[data-cta='pricing']"

auth:
  login_url: /login
  email_env: REHEARSE_EMAIL
  password_env: REHEARSE_PASSWORD

budgets:
  max_run_seconds: 900
  step_timeout_ms: 30000

# LLM persona agents (optional — NVIDIA NIM / OpenAI)
# rehearse run --llm
`;

function Config() {
  const { data: ws = workspace } = useWorkspace();
  const save = useSaveWorkspace();
  return (
    <div>
      <PageHeader
        eyebrow="configure"
        title="Workspace · rehearse.yaml"
        description="Versioned config. Secrets only via env vars — never in YAML or scorecards."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Workspace</div>
            <div className="font-display text-xl font-semibold mt-1">{ws.name}</div>
            <div className="text-xs text-muted-foreground font-mono mt-1">
              {ws.id} · {ws.members} members · {ws.products} products
            </div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Config version</div>
            <div className="font-display text-xl font-semibold mt-1">
              {ws.configVersion} · {ws.configHash}
            </div>
            <div className="text-xs text-muted-foreground font-mono mt-1">{ws.gitUrl}</div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Evidence retention</div>
            <div className="font-display text-xl font-semibold mt-1">{ws.retentionDays} days</div>
            <div className="text-xs text-muted-foreground font-mono mt-1 flex items-center gap-2">
              PII redaction:
              <button
                type="button"
                onClick={() => save.mutate({ piiRedaction: !ws.piiRedaction })}
                className="underline"
              >
                {ws.piiRedaction ? "on" : "off"}
              </button>
            </div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Strict enterprise mode</div>
            <div className="font-display text-xl font-semibold mt-1 text-ready">
              {ws.strictEnterpriseMode ? "enabled" : "off"}
            </div>
            <div className="text-xs text-muted-foreground font-mono mt-1">
              expects pricing · docs · admin paths
            </div>
          </Panel>
        </div>

        <VisionOnly section="config.yamlEditor">
        <Panel className="overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-2">
            <div className="text-xs text-muted-foreground">YAML editor · journey DSL validator</div>
            <div className="flex gap-2">
              <Chip tone="ready">valid</Chip>
              <button
                type="button"
                className="text-xs font-mono px-3 py-1 rounded border border-border hover:bg-surface-2"
              >
                validate
              </button>
              <button
                type="button"
                className="text-xs font-mono px-3 py-1 rounded bg-primary text-primary-foreground"
              >
                save · v15
              </button>
            </div>
          </div>
          <pre className="p-5 text-[12.5px] font-mono leading-relaxed overflow-x-auto bg-surface-2/30 text-foreground/95">
            {yaml}
          </pre>
        </Panel>
        </VisionOnly>

        <VisionOnly section="config.personasEditor">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground mb-3">Personas · 3–7 configurable</div>
            <div className="space-y-3">
              {personas.map((p) => (
                <div key={p.id} className="border border-border rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{p.name}</div>
                    <Chip
                      tone={
                        p.patience === "low" ? "danger" : p.patience === "medium" ? "warn" : "ready"
                      }
                    >
                      {p.patience} patience
                    </Chip>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {p.role} — goal: {p.goal}
                  </div>
                  {p.stressFactors && (
                    <div className="text-[10px] font-mono text-muted-foreground mt-1">
                      stress: {p.stressFactors.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Panel>

          <Panel className="p-5 space-y-5">
            <VisionOnly section="config.secretsVault">
            <div>
              <div className="text-xs text-muted-foreground mb-3">
                Environment secrets · REHEARSE_*
              </div>
              <div className="space-y-2 font-mono text-sm">
                {[
                  "REHEARSE_EMAIL",
                  "REHEARSE_PASSWORD",
                  "NVIDIA_NIM_API_KEY",
                  "OPENAI_API_KEY",
                ].map((s) => (
                  <div
                    key={s}
                    className="flex items-center justify-between border border-border rounded-md px-3 py-2"
                  >
                    <span className="text-xs">{s}</span>
                    <Chip tone="ready">set</Chip>
                  </div>
                ))}
              </div>
            </div>
            </VisionOnly>
            <VisionOnly section="config.agentToggles">
            <div>
              <div className="text-xs text-muted-foreground mb-2">Agent toggles</div>
              <div className="flex flex-wrap gap-1">
                {[...agentConfigDefaults.enabled, ...agentConfigDefaults.optional].map((a) => (
                  <Chip
                    key={a}
                    tone={agentConfigDefaults.enabled.includes(a) ? "ready" : "neutral"}
                  >
                    {a}
                  </Chip>
                ))}
              </div>
            </div>
            </VisionOnly>
          </Panel>
        </div>
        </VisionOnly>

        <VisionOnly section="config.auditLog">
        <Panel className="p-5">
          <div className="text-xs text-muted-foreground mb-3">Audit log · who ran, who viewed</div>
          <div className="divide-y divide-border text-sm font-mono">
            {auditLog.map((e, i) => (
              <div key={i} className="py-2 flex justify-between gap-4">
                <span>
                  {e.at.slice(0, 19)} · {e.who} · {e.action}
                </span>
                <span className="text-muted-foreground">{e.target}</span>
              </div>
            ))}
          </div>
        </Panel>
        </VisionOnly>
      </div>
    </div>
  );
}
