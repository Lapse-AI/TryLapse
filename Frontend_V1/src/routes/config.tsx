import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { workspace, agentConfigDefaults, auditLog } from "@/lib/mock-data";
import { useApiHealth, useWorkspace, useSaveWorkspace } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";
import { ConfigYamlEditor } from "@/components/config-yaml-editor";
import { ExperimentSpecPanel } from "@/components/experiment-spec-panel";
import { PersonaEditorPanel } from "@/components/persona-editor-panel";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";

function RunCredentialsPanel({ configId }: { configId: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginPath, setLoginPath] = useState("/login");
  const [showPw, setShowPw] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const qc = useQueryClient();

  async function save() {
    if (!email && !password) return;
    setSaving(true);
    try {
      const result = await api.saveCredentials(email, password, {
        configId: configId || undefined,
        loginPath: loginPath.trim() || undefined,
      });
      setSaved(true);
      await qc.invalidateQueries({ queryKey: ["credentials"] });
      if (result.yamlUpdated) {
        toast.success("Credentials saved + auth block added to config YAML");
      } else {
        toast.success("Credentials saved — will be used on next run");
      }
      setTimeout(() => setSaved(false), 3000);
    } catch {
      toast.error("Failed to save credentials");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="text-xs text-muted-foreground mb-3">
        Run credentials · REHEARSE_EMAIL / REHEARSE_PASSWORD
      </div>
      <div className="space-y-2">
        <div>
          <label className="text-[11px] text-muted-foreground">Email / Username</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
        </div>
        <div>
          <label className="text-[11px] text-muted-foreground">Password</label>
          <div className="relative">
            <input
              type={showPw ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 pr-7 focus:outline-none focus:ring-1 focus:ring-primary/30"
            />
            <button
              type="button"
              onClick={() => setShowPw(!showPw)}
              className="absolute right-2 top-1/2 -translate-y-1/4 text-muted-foreground"
            >
              {showPw ? <EyeOff className="size-3" /> : <Eye className="size-3" />}
            </button>
          </div>
        </div>
        <div>
          <label className="text-[11px] text-muted-foreground">
            Login page path{" "}
            <span className="text-muted-foreground/60">
              — adds auth block to current config YAML
            </span>
          </label>
          <input
            type="text"
            placeholder="/login"
            value={loginPath}
            onChange={(e) => setLoginPath(e.target.value)}
            className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 font-mono focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
        </div>
        <button
          onClick={save}
          disabled={saving || (!email && !password)}
          className="mt-1 px-3 py-1.5 text-xs rounded border border-primary/40 bg-primary/10 hover:bg-primary/20 text-primary disabled:opacity-40"
        >
          {saving ? "Saving…" : saved ? "Saved ✓" : "Save credentials"}
        </button>
        <p className="text-[11px] text-muted-foreground">
          Credentials stored in <code className="font-mono">.env</code> (never in YAML). Login path
          updates the <code className="font-mono">auth:</code> block in the selected config.
        </p>
      </div>
    </div>
  );
}

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

        {configId ? <PersonaEditorPanel configId={configId} live={!!live} /> : null}

        <VisionOnly section="config.personasEditor">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Panel className="p-5 space-y-5">
              <VisionOnly section="config.secretsVault">
                <RunCredentialsPanel configId={configId ?? ""} />
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
