import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useInitWizard, useApiHealth, useSaveConfig } from "@/lib/api/hooks";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { JourneyDraftPanel } from "@/components/journey-draft-panel";
import { PersonaStudioPanel, type PersonaDraft } from "@/components/persona-studio-panel";
import { setSelectedConfigId } from "@/lib/selected-config";
import { useTestGroup } from "@/hooks/use-test-group";
import { groupInitPreset } from "@/lib/test-groups";

export const Route = createFileRoute("/init")({
  head: () => ({ meta: [{ title: "Init wizard — Launch Rehearsal" }] }),
  component: InitPage,
});

function isLocalhostUrl(url: string): boolean {
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/^\[|\]$/g, "");
    return host === "localhost" || host === "127.0.0.1" || host === "::1";
  } catch {
    return false;
  }
}

const RECORDER_SAMPLE = `[
  { "action": "navigate", "url": "{target_url}/" },
  { "action": "click", "intent": "Compare runs" }
]`;

function RecorderCompile({ live }: { live: boolean }) {
  const [json, setJson] = useState(RECORDER_SAMPLE);
  const [yaml, setYaml] = useState("");
  const [pending, setPending] = useState(false);

  const compile = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    let steps: unknown;
    try {
      steps = JSON.parse(json);
    } catch {
      toast.error("Invalid JSON");
      return;
    }
    if (!Array.isArray(steps)) {
      toast.error("Root must be a JSON array of steps");
      return;
    }
    setPending(true);
    try {
      const out = await api.compileRecording({
        journeyId: "recorded-journey",
        journeyName: "Recorded journey",
        steps: steps as { action: string }[],
      });
      if (!out.valid) {
        toast.error(out.errors.join("; ") || "Validation failed");
        return;
      }
      setYaml(out.yaml);
      toast.success("YAML fragment ready — copy into your config");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Compile failed");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="space-y-3">
      <label htmlFor="recorder-steps" className="text-xs text-muted-foreground">
        Steps JSON
      </label>
      <textarea
        id="recorder-steps"
        className="w-full min-h-[120px] font-mono text-xs bg-surface border border-border rounded-md p-3"
        value={json}
        onChange={(e) => setJson(e.target.value)}
      />
      <button
        type="button"
        disabled={!live || pending}
        onClick={() => void compile()}
        className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
      >
        {pending ? "Compiling…" : "Compile to YAML"}
      </button>
      {yaml && (
        <pre className="text-[11px] font-mono bg-surface-2 border border-border rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">
          {yaml}
        </pre>
      )}
    </div>
  );
}

function InitPage() {
  const { data: live } = useApiHealth();
  const { data: wizard } = useInitWizard();
  const saveConfig = useSaveConfig();
  const { isSignedIn, group, resolvedConfigId } = useTestGroup();
  const allConfigs = wizard?.configs ?? [];
  const exampleConfigs = allConfigs.slice(0, 8);
  const hiddenConfigCount = Math.max(0, allConfigs.length - exampleConfigs.length);
  const dogfoodDefault =
    (wizard?.dogfood as { targetUrl?: string } | undefined)?.targetUrl ?? "http://127.0.0.1:8081";

  const [targetUrl, setTargetUrl] = useState("");
  const [productName, setProductName] = useState("");
  const [withAuth, setWithAuth] = useState(false);
  const [selfTest, setSelfTest] = useState(false);
  const [allowLocalhost, setAllowLocalhost] = useState(false);
  const [preflight, setPreflight] = useState<{
    ok: boolean;
    status_code?: number;
    error?: string;
  } | null>(null);
  const [piiRedaction, setPiiRedaction] = useState(false);
  const [executeAllPersonasInBrowser, setExecuteAllPersonasInBrowser] = useState(false);
  const [excludePathPrefixes, setExcludePathPrefixes] = useState("");
  const [viewports, setViewports] = useState({
    desktop: true,
    tablet: false,
    mobile: false,
  });
  const [personaLens, setPersonaLens] = useState(true);
  const [coreEnabled, setCoreEnabled] = useState<Record<string, boolean>>({
    "p1-evaluator": true,
    "p2-operator": true,
    "p3-admin": true,
  });
  const [stagedExtras, setStagedExtras] = useState<PersonaDraft[]>([]);

  const localhostTarget = useMemo(() => isLocalhostUrl(targetUrl), [targetUrl]);
  const preflightNeedsLocalhost = selfTest || allowLocalhost || localhostTarget;

  useEffect(() => {
    const defaultUrl = wizard?.defaults?.targetUrl;
    if (typeof defaultUrl === "string" && defaultUrl && !targetUrl) {
      setTargetUrl(defaultUrl);
    }
  }, [wizard?.defaults?.targetUrl, targetUrl]);

  useEffect(() => {
    if (selfTest) {
      setAllowLocalhost(true);
    }
  }, [selfTest]);

  const runPreflight = async () => {
    if (!targetUrl) return;
    const result = await api.preflight(targetUrl, {
      allowLocalhost: preflightNeedsLocalhost,
    });
    setPreflight(result);
  };

  const handleGenerate = (opts?: { dogfood?: boolean }) => {
    if (!targetUrl || !live) return;
    const dogfood = opts?.dogfood ?? selfTest;
    const selectedViewports = (Object.entries(viewports) as [keyof typeof viewports, boolean][])
      .filter(([, on]) => on)
      .map(([name]) => name);
    saveConfig.mutate(
      {
        targetUrl,
        productName: productName || (dogfood ? "Launch Rehearsal Dashboard" : undefined),
        withAuth: dogfood ? false : withAuth,
        piiRedaction,
        allowLocalhost: dogfood || allowLocalhost || localhostTarget,
        selfTest: dogfood,
        excludePathPrefixes: excludePathPrefixes.trim() || undefined,
        viewports: selectedViewports.length ? selectedViewports : undefined,
        executeAllPersonasInBrowser,
        personaLens,
        personaEnabled: coreEnabled,
        extraPersonas: stagedExtras,
      },
      {
        onSuccess: (result) => {
          setSelectedConfigId(result.id);
          toast.success(`Config written to ${result.path}`, {
            action: {
              label: "Open Runner",
              onClick: () => {
                window.location.href = "/runner";
              },
            },
          });
        },
        onError: (err) => {
          toast.error(err instanceof Error ? err.message : "Failed to write config");
        },
      },
    );
  };

  const applyDogfoodPreset = () => {
    setTargetUrl(dogfoodDefault);
    setSelfTest(true);
    setAllowLocalhost(true);
    setPreflight(null);
  };

  const applyTestGroupPreset = () => {
    const preset = groupInitPreset(group);
    setTargetUrl(preset.targetUrl);
    if (preset.productName) setProductName(preset.productName);
    setWithAuth(preset.withAuth ?? false);
    setSelfTest(preset.selfTest ?? false);
    setAllowLocalhost(preset.allowLocalhost ?? false);
    setPreflight(null);
    setSelectedConfigId(resolvedConfigId);
    toast.success(`Applied ${group.label} preset`);
  };

  const steps = wizard?.steps ?? [
    { id: "target", title: "Target URL", description: "Production or staging surface" },
    { id: "auth", title: "Auth", description: "Optional credentials via env" },
    { id: "journeys", title: "Journeys", description: "Persona × path matrix" },
    { id: "review", title: "Review", description: "Preflight & run" },
  ];

  const dogfoodHint =
    (wizard?.dogfood as { hint?: string } | undefined)?.hint ??
    "Paste this dashboard URL to rehearse Launch Rehearsal with Launch Rehearsal.";

  return (
    <div>
      <PageHeader
        eyebrow="configure"
        title="rehearse init wizard"
        description={wizard?.cliHint ?? "Scaffold rehearse.yaml — mirrors CLI init flow."}
      />
      <div className="p-8 max-w-[900px] space-y-6">
        {isSignedIn && (
          <Panel className="p-6 space-y-3 border-violet/30 bg-violet/5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-medium">Test group preset</div>
                <p className="text-sm text-muted-foreground mt-1">
                  {group.personaLabel} — fills target URL and auth flags from the top-bar test
                  group.
                </p>
              </div>
              <Chip tone="violet">{group.label}</Chip>
            </div>
            <div className="text-[11px] font-mono text-muted-foreground">
              {group.targetUrl} · config {resolvedConfigId}
              {group.withAuth && " · REHEARSE_EMAIL / REHEARSE_PASSWORD"}
            </div>
            <button
              type="button"
              onClick={applyTestGroupPreset}
              className="text-xs px-3 py-1.5 rounded-md border border-violet/40 bg-background hover:bg-surface-2"
            >
              Apply test group to form
            </button>
          </Panel>
        )}

        <Panel className="p-6 space-y-4 border-primary/30 bg-primary/5">
          <div>
            <div className="font-medium">Dogfood this dashboard</div>
            <p className="text-sm text-muted-foreground mt-1">{dogfoodHint}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={applyDogfoodPreset}
              className="text-xs px-3 py-1.5 rounded-md border border-primary/40 bg-background"
            >
              Use {dogfoodDefault}
            </button>
            <button
              type="button"
              disabled={!live || !targetUrl.trim() || saveConfig.isPending}
              onClick={() => handleGenerate({ dogfood: true })}
              className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
            >
              Generate self-test YAML
            </button>
            <Link
              to="/runner"
              className="text-xs px-3 py-1.5 rounded-md border border-border inline-flex items-center"
            >
              Open Runner →
            </Link>
          </div>
          <p className="text-[11px] text-muted-foreground font-mono">
            Requires Frontend_V1 (npm run dev) and rehearse serve. Config sets allow_localhost and
            journeys for /, /runs, /compare, /init, /runner.
          </p>
        </Panel>

        <Panel className="p-6 space-y-4">
          <div>
            <label htmlFor="init-target-url" className="text-xs text-muted-foreground">
              Target URL
            </label>
            <input
              id="init-target-url"
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm font-mono"
              placeholder={String(wizard?.defaults?.targetUrl ?? "https://app.example.com")}
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="init-product-name" className="text-xs text-muted-foreground">
              Product name (optional)
            </label>
            <input
              id="init-product-name"
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
              placeholder="Auto-derived from URL"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3">
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
            {localhostTarget && !preflightNeedsLocalhost && (
              <span className="text-xs text-amber-600">Enable allow localhost for local URLs</span>
            )}
          </div>
          <label htmlFor="init-self-test" className="flex items-center gap-2 text-sm">
            <input
              id="init-self-test"
              type="checkbox"
              checked={selfTest}
              onChange={(e) => setSelfTest(e.target.checked)}
            />
            Self-test config (journeys for this dashboard UI)
          </label>
          <label htmlFor="init-allow-localhost" className="flex items-center gap-2 text-sm">
            <input
              id="init-allow-localhost"
              type="checkbox"
              checked={allowLocalhost || selfTest}
              disabled={selfTest}
              onChange={(e) => setAllowLocalhost(e.target.checked)}
            />
            Allow localhost / 127.0.0.1 (SSRF guard opt-in)
          </label>
          <label htmlFor="init-with-auth" className="flex items-center gap-2 text-sm">
            <input
              id="init-with-auth"
              type="checkbox"
              checked={withAuth}
              disabled={selfTest}
              onChange={(e) => setWithAuth(e.target.checked)}
            />
            Include auth block (REHEARSE_EMAIL / REHEARSE_PASSWORD)
          </label>
          <label htmlFor="init-pii-redaction" className="flex items-center gap-2 text-sm">
            <input
              id="init-pii-redaction"
              type="checkbox"
              checked={piiRedaction}
              onChange={(e) => setPiiRedaction(e.target.checked)}
            />
            PII redaction in scorecards (Phase 2 toggle)
          </label>
          <label htmlFor="init-all-personas-browser" className="flex items-center gap-2 text-sm">
            <input
              id="init-all-personas-browser"
              type="checkbox"
              checked={executeAllPersonasInBrowser}
              onChange={(e) => setExecuteAllPersonasInBrowser(e.target.checked)}
            />
            Execute all personas in browser (Phase C — slower, full E2E matrix)
          </label>
          <div>
            <label htmlFor="init-exclude-prefixes" className="text-xs text-muted-foreground">
              Crawl exclude path prefixes (comma-separated, optional)
            </label>
            <input
              id="init-exclude-prefixes"
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm font-mono"
              placeholder="/api/, /admin/internal/"
              value={excludePathPrefixes}
              onChange={(e) => setExcludePathPrefixes(e.target.value)}
            />
          </div>
          <fieldset className="space-y-2">
            <legend className="text-xs text-muted-foreground">
              Viewport profiles (browser replay)
            </legend>
            {(["desktop", "tablet", "mobile"] as const).map((vp) => (
              <label key={vp} htmlFor={`init-vp-${vp}`} className="flex items-center gap-2 text-sm">
                <input
                  id={`init-vp-${vp}`}
                  type="checkbox"
                  checked={viewports[vp]}
                  onChange={(e) => setViewports((prev) => ({ ...prev, [vp]: e.target.checked }))}
                />
                {vp} {vp === "desktop" ? "(default)" : ""}
              </label>
            ))}
          </fieldset>
        </Panel>

        <PersonaStudioPanel
          live={!!live}
          targetUrl={targetUrl}
          productName={productName}
          configId={undefined}
          personaLens={personaLens}
          onPersonaLensChange={setPersonaLens}
          coreEnabled={coreEnabled}
          onCoreEnabledChange={(id, enabled) =>
            setCoreEnabled((prev) => ({ ...prev, [id]: enabled }))
          }
          stagedExtras={stagedExtras}
          onStageExtra={(p) =>
            setStagedExtras((prev) => (prev.some((x) => x.id === p.id) ? prev : [...prev, p]))
          }
          onRemoveStaged={(id) => setStagedExtras((prev) => prev.filter((p) => p.id !== id))}
        />

        <JourneyDraftPanel live={!!live} targetUrl={targetUrl} />

        <Panel className="p-6 space-y-4">
          <div>
            <div className="font-display font-semibold">Journey recorder (Phase C)</div>
            <p className="text-sm text-muted-foreground mt-1">
              Paste steps as JSON — compiles to a YAML journey fragment for your config.
            </p>
          </div>
          <RecorderCompile live={!!live} />
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

        {allConfigs.length > 0 && (
          <Panel className="p-6">
            <div className="text-xs text-muted-foreground mb-3">Start from example config</div>
            <ul className="font-mono text-xs space-y-1">
              {exampleConfigs.map((c) => (
                <li key={c.id}>{c.path}</li>
              ))}
            </ul>
            {hiddenConfigCount > 0 && (
              <div className="mt-2 text-[11px] text-muted-foreground">
                +{hiddenConfigCount} more generated configs in artifacts. Open `Config (YAML)` to
                edit a specific file.
              </div>
            )}
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
            onClick={() => handleGenerate()}
            className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground font-medium disabled:opacity-50"
          >
            {saveConfig.isPending ? "Writing…" : "Generate & write YAML"}
          </button>
        </Panel>
      </div>
    </div>
  );
}
