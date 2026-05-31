import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useInitWizard, useApiHealth, useSaveConfig } from "@/lib/api/hooks";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

export const Route = createFileRoute("/init")({
  head: () => ({ meta: [{ title: "Init wizard — Launch Rehearsal" }] }),
  component: InitPage,
});

function InitPage() {
  const { data: live } = useApiHealth();
  const { data: wizard } = useInitWizard();
  const saveConfig = useSaveConfig();
  const [targetUrl, setTargetUrl] = useState("");
  const [productName, setProductName] = useState("");
  const [withAuth, setWithAuth] = useState(false);
  const [preflight, setPreflight] = useState<{
    ok: boolean;
    status_code?: number;
    error?: string;
  } | null>(null);
  const [piiRedaction, setPiiRedaction] = useState(false);

  useEffect(() => {
    const defaultUrl = wizard?.defaults?.targetUrl;
    if (typeof defaultUrl === "string" && defaultUrl && !targetUrl) {
      setTargetUrl(defaultUrl);
    }
  }, [wizard?.defaults?.targetUrl, targetUrl]);

  const runPreflight = async () => {
    if (!targetUrl) return;
    const result = await api.preflight(targetUrl);
    setPreflight(result);
  };

  const handleGenerate = () => {
    if (!targetUrl || !live) return;
    saveConfig.mutate(
      {
        targetUrl,
        productName: productName || undefined,
        withAuth,
        piiRedaction,
      },
      {
        onSuccess: (result) => {
          toast.success(`Config written to ${result.path}`);
        },
        onError: (err) => {
          toast.error(err instanceof Error ? err.message : "Failed to write config");
        },
      },
    );
  };

  const steps = wizard?.steps ?? [
    { id: "target", title: "Target URL", description: "Production or staging surface" },
    { id: "auth", title: "Auth", description: "Optional credentials via env" },
    { id: "journeys", title: "Journeys", description: "Persona × path matrix" },
    { id: "review", title: "Review", description: "Preflight & run" },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="configure"
        title="rehearse init wizard"
        description={wizard?.cliHint ?? "Scaffold rehearse.yaml — mirrors CLI init flow."}
      />
      <div className="p-8 max-w-[900px] space-y-6">
        <Panel className="p-6 space-y-4">
          <div>
            <label className="text-xs text-muted-foreground">Target URL</label>
            <input
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm font-mono"
              placeholder={String(wizard?.defaults?.targetUrl ?? "https://app.example.com")}
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Product name (optional)</label>
            <input
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
              placeholder="Auto-derived from URL"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              disabled={!live}
              onClick={runPreflight}
              className="text-xs px-3 py-1.5 rounded-md border border-border disabled:opacity-50"
            >
              Preflight HEAD
            </button>
            {preflight && (
              <Chip tone={preflight.ok ? "ready" : "danger"}>
                {preflight.ok ? `OK ${preflight.status_code}` : preflight.error}
              </Chip>
            )}
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={withAuth}
              onChange={(e) => setWithAuth(e.target.checked)}
            />
            Include auth block (REHEARSE_EMAIL / REHEARSE_PASSWORD)
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={piiRedaction}
              onChange={(e) => setPiiRedaction(e.target.checked)}
            />
            PII redaction in scorecards (Phase 2 toggle)
          </label>
        </Panel>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-4">Wizard steps</div>
          <ol className="space-y-4">
            {steps.map((s, i) => (
              <li key={s.id} className="flex gap-4">
                <span className="font-mono text-xs text-muted-foreground w-6">{i + 1}</span>
                <div>
                  <div className="font-medium">{s.title}</div>
                  <div className="text-sm text-muted-foreground">{s.description}</div>
                </div>
              </li>
            ))}
          </ol>
        </Panel>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-2">Defaults from workspace</div>
          <pre className="text-[11px] font-mono bg-surface-2 border border-border rounded-lg p-4 overflow-x-auto">
            {JSON.stringify(wizard?.defaults ?? {}, null, 2)}
          </pre>
        </Panel>

        {(wizard?.configs ?? []).length > 0 && (
          <Panel className="p-6">
            <div className="text-xs text-muted-foreground mb-3">Start from example config</div>
            <ul className="font-mono text-xs space-y-1">
              {wizard!.configs.map((c) => (
                <li key={c.id}>{c.path}</li>
              ))}
            </ul>
          </Panel>
        )}

        <Panel className="p-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="font-medium">Generate & write YAML</div>
            <div className="text-sm text-muted-foreground mt-1">
              {wizard?.writeHint ?? "POST /api/configs — writes artifacts/configs/{slug}.yaml"}
            </div>
          </div>
          <button
            type="button"
            disabled={!live || !targetUrl.trim() || saveConfig.isPending}
            onClick={handleGenerate}
            className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground font-medium disabled:opacity-50"
          >
            {saveConfig.isPending ? "Writing…" : "Generate & write YAML"}
          </button>
        </Panel>
      </div>
    </div>
  );
}
