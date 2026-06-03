import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { workspace, agentConfigDefaults, auditLog } from "@/lib/mock-data";
import { useApiHealth, useWorkspace, useSaveWorkspace } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";
import { ConfigYamlEditor } from "@/components/config-yaml-editor";
import { ExperimentSpecPanel } from "@/components/experiment-spec-panel";
import { PersonaEditorPanel } from "@/components/persona-editor-panel";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";

export const Route = createFileRoute("/config")({
  head: () => ({ meta: [{ title: "Workspace — Launch Rehearsal" }] }),
  component: Config,
});

function Config() {
  const { data: ws = workspace } = useWorkspace();
  const save = useSaveWorkspace();
  const { configId } = usePersistedConfigId();
  const { data: live } = useApiHealth();
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

        <ConfigYamlEditor />

        {configId ? <ExperimentSpecPanel configId={configId} /> : null}

        {configId ? (
          <PersonaEditorPanel configId={configId} live={!!live} />
        ) : null}

        <VisionOnly section="config.personasEditor">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
            <div className="text-xs text-muted-foreground mb-3">
              Audit log · who ran, who viewed
            </div>
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
