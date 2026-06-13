import { useState, useEffect, useCallback, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { workspace as mockWorkspace, agentConfigDefaults, auditLog } from "@/lib/mock-data";
import {
  useApiHealth,
  useWorkspace,
  useSaveWorkspace,
  useInitWizard,
  useSaveConfig,
  useTriggerJob,
  useConfigYaml,
} from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";
import { ConfigYamlEditor } from "@/components/config-yaml-editor";
import { ExperimentSpecPanel } from "@/components/experiment-spec-panel";
import { PersonaEditorPanel } from "@/components/persona-editor-panel";
import { PersonaStudioPanel, type PersonaDraft } from "@/components/persona-studio-panel";
import { ProductIntelligencePanel } from "@/components/product-intelligence-panel";
import { JourneyDiscoveryPanel } from "@/components/journey-discovery-panel";
import { JourneyDraftPanel } from "@/components/journey-draft-panel";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { useTestGroup } from "@/hooks/use-test-group";
import { groupInitPreset } from "@/lib/test-groups";
import { setSelectedConfigId } from "@/lib/selected-config";
import { getWorkspace } from "@/lib/workspace";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import {
  Eye,
  EyeOff,
  Play,
  Loader2,
  ChevronDown,
  ChevronUp,
  Globe,
  Users,
  Map,
  Code2,
  KeyRound,
  Zap,
  CheckCircle2,
} from "lucide-react";

export const Route = createFileRoute("/$workspaceSlug/config")({
  head: () => ({ meta: [{ title: "Config — Launch Rehearsal" }] }),
  component: ConfigPage,
});

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

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

function SectionHeader({
  icon: Icon,
  title,
  description,
  status,
  count,
}: {
  icon: React.ElementType;
  title: string;
  description?: string;
  status?: "configured" | "partial" | "empty";
  count?: number;
}) {
  return (
    <div className="flex items-start justify-between gap-3 mb-4">
      <div className="flex items-start gap-3">
        <div className="size-8 rounded-xl bg-primary/8 flex items-center justify-center shrink-0 mt-0.5">
          <Icon className="size-4 text-primary" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{title}</span>
            {count != null && count > 0 && (
              <span className="text-[11px] font-mono text-muted-foreground">{count}</span>
            )}
          </div>
          {description && <p className="text-[12px] text-muted-foreground mt-0.5">{description}</p>}
        </div>
      </div>
      {status === "configured" && <CheckCircle2 className="size-4 text-ready shrink-0 mt-1" />}
    </div>
  );
}

function SavedConfigPreview({ configId, onDismiss }: { configId: string; onDismiss: () => void }) {
  const { data: file, isLoading } = useConfigYaml(configId);
  const [collapsed, setCollapsed] = useState(false);
  if (!file && !isLoading) return null;
  return (
    <div className="rounded-2xl border border-ready/40 bg-ready/5 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-ready/20">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="size-4 text-ready" />
          <span className="text-sm font-medium">
            Saved: <span className="font-mono text-xs">{configId}.yaml</span>
          </span>
          <span className="text-[11px] text-muted-foreground">
            — {file?.yaml?.split("\n").filter(Boolean).length ?? "…"} lines
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="text-xs text-muted-foreground hover:text-foreground px-2 py-0.5 rounded border border-border/60"
          >
            {collapsed ? "Show YAML" : "Hide YAML"}
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-muted-foreground hover:text-foreground px-2 py-0.5 rounded border border-border/60"
          >
            ✕
          </button>
        </div>
      </div>
      {!collapsed && (
        <pre className="p-4 text-[11px] font-mono leading-relaxed text-foreground/80 overflow-auto max-h-96 whitespace-pre-wrap">
          {isLoading ? "Loading…" : (file?.yaml ?? "")}
        </pre>
      )}
    </div>
  );
}

function AdvancedAccordion({
  children,
  label = "Advanced settings",
}: {
  children: React.ReactNode;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-border overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-surface-2/50 transition-colors"
      >
        <div className="flex items-center gap-2.5 text-sm text-muted-foreground font-medium">
          <Code2 className="size-4" />
          {label}
        </div>
        {open ? (
          <ChevronUp className="size-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="size-4 text-muted-foreground" />
        )}
      </button>
      {open && <div className="px-5 pb-5 border-t border-border space-y-5 pt-5">{children}</div>}
    </div>
  );
}

function isLocalhostUrl(url: string): boolean {
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/^\[|\]$/g, "");
    return host === "localhost" || host === "127.0.0.1" || host === "::1";
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

function ConfigPage() {
  const { data: live } = useApiHealth();
  const { data: ws = mockWorkspace } = useWorkspace();
  const saveWorkspace = useSaveWorkspace();
  const saveConfig = useSaveConfig();
  const { configId, pickConfig } = usePersistedConfigId();
  const { isSignedIn, group, resolvedConfigId } = useTestGroup();
  const userWorkspace = getWorkspace();

  const workspaceConfigId = userWorkspace?.configPath
    ? (userWorkspace.configPath
        .split("/")
        .pop()
        ?.replace(/\.ya?ml$/, "") ?? null)
    : null;

  const { data: wizard } = useInitWizard();
  const allConfigs = wizard?.configs ?? [];
  const exampleConfigs = allConfigs.slice(0, 8);
  const hiddenConfigCount = Math.max(0, allConfigs.length - exampleConfigs.length);
  const dogfoodDefault =
    (wizard as unknown as { dogfood?: { targetUrl?: string } } | undefined)?.dogfood?.targetUrl ??
    "http://127.0.0.1:8081";

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
  const [executeAllPersonasInBrowser, setExecuteAllPersonasInBrowser] = useState(true);
  const [excludePathPrefixes, setExcludePathPrefixes] = useState("");
  const [viewports, setViewports] = useState({ desktop: true, tablet: false, mobile: false });
  const [personaLens, setPersonaLens] = useState(true);
  const [personas, setPersonas] = useState<PersonaDraft[]>([]);
  const [configPersonas, setConfigPersonas] = useState<PersonaDraft[]>([]);
  const [personaRefreshKey, setPersonaRefreshKey] = useState(0);
  const [productModel, setProductModel] = useState<Record<string, unknown> | null>(null);
  const [crawlCreds, setCrawlCreds] = useState<{
    loginEmail: string;
    loginPassword: string;
    loginUrl: string;
    emailSelector: string;
    passwordSelector: string;
    submitSelector: string;
  } | null>(null);
  const [savedConfigId, setSavedConfigId] = useState<string | null>(null);

  const localhostTarget = useMemo(() => isLocalhostUrl(targetUrl), [targetUrl]);
  const preflightNeedsLocalhost = selfTest || allowLocalhost || localhostTarget;

  useEffect(() => {
    if (userWorkspace?.targetUrl && !targetUrl) setTargetUrl(userWorkspace.targetUrl);
    else if (wizard?.defaults?.targetUrl && !targetUrl)
      setTargetUrl(String(wizard.defaults.targetUrl));
    if (userWorkspace?.productName && !productName) setProductName(userWorkspace.productName);
  }, [
    userWorkspace?.targetUrl,
    userWorkspace?.productName,
    wizard?.defaults?.targetUrl,
    targetUrl,
    productName,
  ]);

  useEffect(() => {
    if (selfTest) setAllowLocalhost(true);
  }, [selfTest]);

  const runPreflight = async () => {
    if (!targetUrl) return;
    const result = await api.preflight(targetUrl, { allowLocalhost: preflightNeedsLocalhost });
    setPreflight(result);
  };

  const handleGenerate = (opts?: { dogfood?: boolean }) => {
    if (!targetUrl || !live) return;
    const dogfood = opts?.dogfood ?? selfTest;
    const selectedViewports = (Object.entries(viewports) as [keyof typeof viewports, boolean][])
      .filter(([, on]) => on)
      .map(([name]) => name);
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    const localTs = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    saveConfig.mutate(
      {
        targetUrl,
        productName: productName || (dogfood ? "Launch Rehearsal Dashboard" : undefined),
        withAuth: dogfood ? false : withAuth || !!crawlCreds?.loginEmail,
        piiRedaction,
        allowLocalhost: dogfood || allowLocalhost || localhostTarget,
        selfTest: dogfood,
        excludePathPrefixes: excludePathPrefixes.trim() || undefined,
        viewports: selectedViewports.length ? selectedViewports : undefined,
        executeAllPersonasInBrowser,
        localTimestamp: localTs,
        personaLens,
        extraPersonas: configPersonas.length > 0 ? configPersonas : personas,
        existingConfigId: workspaceConfigId ?? undefined,
      },
      {
        onSuccess: (result) => {
          setSelectedConfigId(result.id);
          pickConfig(result.id);
          // Update workspace in localStorage to track the new latest version
          if (userWorkspace) {
            const updated = { ...userWorkspace, configPath: result.path };
            localStorage.setItem("rehearse:workspace", JSON.stringify(updated));
          }
          // Save crawl credentials if filled in ProductIntelligencePanel
          if (crawlCreds?.loginEmail && crawlCreds?.loginPassword) {
            api
              .saveCredentials(crawlCreds.loginEmail, crawlCreds.loginPassword, {
                configId: result.id,
                loginPath: crawlCreds.loginUrl || undefined,
              })
              .catch(() => {});
          }
          setSavedConfigId(result.id);
          toast.success(`Saved as ${result.id}.yaml`, {
            description: "Now marked as (latest) in the YAML editor dropdown.",
            duration: 6000,
            action: {
              label: "Open Runner",
              onClick: () => {
                window.location.href = userWorkspace ? `/${userWorkspace.slug}/runner` : "/runner";
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

  // Load saved config personas for journey discovery when workspace config exists
  useEffect(() => {
    if (!workspaceConfigId || !live) return;
    api
      .getConfigPersonas(workspaceConfigId)
      .then((data) => setConfigPersonas(data.personas as PersonaDraft[]))
      .catch(() => {});
  }, [workspaceConfigId, live]);

  // Journey discovery uses saved config personas first, falling back to newly staged ones
  const personasForDiscovery = configPersonas.length > 0 ? configPersonas : personas;

  // Shared ProductIntelligencePanel callbacks — hoisted above the branch below
  // so hooks run unconditionally regardless of which layout renders.
  const handleProductModelReady = useCallback(
    (m: Record<string, unknown>) => setProductModel(m),
    [],
  );
  const handleCredsChange = useCallback(
    (c: {
      loginEmail: string;
      loginPassword: string;
      loginUrl: string;
      emailSelector: string;
      passwordSelector: string;
      submitSelector: string;
    }) => setCrawlCreds(c),
    [],
  );
  const handleImportPersonas = useCallback(
    async (detected: Array<{ id: string; name: string; role: string; goals: string[] }>) => {
      if (!workspaceConfigId || !live) {
        toast.error("Config not saved yet — save a config first");
        return;
      }
      let added = 0;
      let lastErr = "";
      for (const p of detected) {
        try {
          await api.appendPersonaToConfig({ configId: workspaceConfigId, persona: p });
          added++;
        } catch (e) {
          lastErr = e instanceof Error ? e.message : String(e);
        }
      }
      try {
        const fresh = await api.getConfigPersonas(workspaceConfigId);
        setConfigPersonas(fresh.personas as PersonaDraft[]);
        setPersonaRefreshKey((k) => k + 1);
      } catch {
        /* panel will show what it has */
      }
      if (added > 0) {
        toast.success(`Imported ${added} persona${added !== 1 ? "s" : ""} from product analysis`);
      } else if (lastErr) {
        toast.error(`Import failed: ${lastErr}`);
      } else {
        toast.info("Personas already up to date");
      }
    },
    [workspaceConfigId, live],
  );

  // -------------------------------------------------------------------------
  // Workspace layout — create + edit in one place
  // -------------------------------------------------------------------------
  if (userWorkspace) {
    const readyToSave = !!live && !!targetUrl.trim();
    const setupSummary = [
      personas.length > 0 && `${personas.length} persona${personas.length !== 1 ? "s" : ""}`,
      workspaceConfigId && "config saved",
    ]
      .filter(Boolean)
      .join(" · ");

    return (
      <div>
        <PageHeader
          eyebrow={userWorkspace.slug}
          title={userWorkspace.productName || userWorkspace.name}
          description={`Rehearsal setup for ${userWorkspace.targetUrl}`}
          actions={
            <div className="flex items-center gap-2">
              <Link
                to="/$workspaceSlug/runner"
                params={{ workspaceSlug: userWorkspace.slug }}
                className="flex items-center gap-2 px-4 py-2 rounded-full border border-border bg-background text-sm hover:bg-surface-2 transition-colors"
              >
                <Play className="size-3.5" /> Runner
              </Link>
              <button
                type="button"
                disabled={!readyToSave || saveConfig.isPending}
                onClick={() => handleGenerate()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-foreground text-background font-medium text-sm disabled:opacity-40 hover:opacity-90 transition-opacity shadow-sm"
              >
                {saveConfig.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Zap className="size-4" />
                )}
                {saveConfig.isPending ? "Saving…" : "Save config"}
              </button>
            </div>
          }
        />

        <div className="p-8 max-w-[1100px] space-y-10">
          {/* ── 1. Target & product intelligence ─────────────────────────── */}
          <section>
            <SectionHeader
              icon={Globe}
              title="Target"
              description="The product you're rehearsing — URL drives the crawl and product analysis."
              status={targetUrl ? "configured" : "empty"}
            />
            <ProductIntelligencePanel
              live={!!live}
              targetUrl={targetUrl}
              productName={productName}
              configId={workspaceConfigId}
              onModelReady={handleProductModelReady}
              onCredsChange={handleCredsChange}
              startCollapsed={!!workspaceConfigId}
              onImportPersonas={handleImportPersonas}
            />
          </section>

          {/* ── 2. Personas ───────────────────────────────────────────────── */}
          <section>
            <SectionHeader
              icon={Users}
              title="Personas"
              description="Who uses this product? Each persona gets their own journey set and scorecard."
            />
            {workspaceConfigId ? (
              <PersonaEditorPanel
                configId={workspaceConfigId}
                live={!!live}
                onPersonasChanged={(updated) => setConfigPersonas(updated as PersonaDraft[])}
                refreshKey={personaRefreshKey}
              />
            ) : (
              // Fresh setup: stage personas before config generation
              <PersonaStudioPanel
                live={!!live}
                targetUrl={targetUrl}
                productName={productName}
                productModel={productModel}
                personaLens={personaLens}
                onPersonaLensChange={setPersonaLens}
                personas={personas}
                onAddPersona={(p) =>
                  setPersonas((prev) => (prev.some((x) => x.id === p.id) ? prev : [...prev, p]))
                }
                onRemovePersona={(id) => setPersonas((prev) => prev.filter((p) => p.id !== id))}
              />
            )}
          </section>

          {/* ── 3. Journey discovery ──────────────────────────────────────── */}
          <section>
            <SectionHeader
              icon={Map}
              title="Journey discovery"
              description="Crawl the product and discover real user paths for each persona — no assumptions."
            />
            <JourneyDiscoveryPanel
              live={!!live}
              configId={workspaceConfigId}
              productModel={productModel}
              personas={personasForDiscovery}
            />
          </section>

          {/* ── 4. Advanced settings (accordion) ─────────────────────────── */}
          <AdvancedAccordion label="YAML, credentials & advanced options">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Code2 className="size-3.5 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground">Config YAML</span>
              </div>
              <ConfigYamlEditor workspaceConfigId={workspaceConfigId} />
            </div>

            <div>
              <div className="flex items-center gap-2 mb-3">
                <KeyRound className="size-3.5 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground">Run credentials</span>
              </div>
              <RunCredentialsPanel configId={workspaceConfigId ?? configId ?? ""} />
            </div>

            <JourneyDraftPanel live={!!live} targetUrl={targetUrl} />

            {/* Workspace meta */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-border">
              {[
                { label: "Members", value: String(ws.members) },
                { label: "Retention", value: `${ws.retentionDays}d` },
                {
                  label: "PII redaction",
                  value: ws.piiRedaction ? "on" : "off",
                  action: () => saveWorkspace.mutate({ piiRedaction: !ws.piiRedaction }),
                },
                { label: "Enterprise mode", value: ws.strictEnterpriseMode ? "enabled" : "off" },
              ].map((s) => (
                <div key={s.label} className="rounded-xl border border-border p-3">
                  <div className="text-[11px] text-muted-foreground">{s.label}</div>
                  {s.action ? (
                    <button
                      type="button"
                      onClick={s.action}
                      className="text-sm font-medium mt-0.5 underline decoration-dotted"
                    >
                      {s.value}
                    </button>
                  ) : (
                    <div className="text-sm font-medium mt-0.5">{s.value}</div>
                  )}
                </div>
              ))}
            </div>

            {workspaceConfigId && (
              <div className="rounded-xl bg-surface-2 border border-border px-4 py-3">
                <div className="text-[11px] text-muted-foreground mb-1">Run command</div>
                <code className="text-[11px] font-mono text-foreground select-all break-all">
                  ./rehearse run -c launch-rehearsal/artifacts/configs/{workspaceConfigId}.yaml -o
                  launch-rehearsal/artifacts/
                </code>
              </div>
            )}
          </AdvancedAccordion>

          {/* ── 5. Save / Run CTA ─────────────────────────────────────────── */}
          <div className="rounded-2xl border border-border bg-surface p-5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-sm font-medium">
                {workspaceConfigId ? "Save a new version" : "Create config"}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Creates a dated snapshot{" "}
                <span className="font-mono">
                  {workspaceConfigId
                    ? `${workspaceConfigId.split("-")[0]}-YYYYMMDD-HHmmss.yaml`
                    : "[slug]-YYYYMMDD-HHmmss.yaml"}
                </span>{" "}
                — visible in the YAML editor history dropdown.
              </p>
              {setupSummary && (
                <p className="text-[11px] text-muted-foreground/70 mt-1">{setupSummary}</p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/$workspaceSlug/runner"
                params={{ workspaceSlug: userWorkspace.slug }}
                className="text-xs px-4 py-2 rounded-full border border-border hover:bg-surface-2 inline-flex items-center gap-1.5 transition-colors"
              >
                <Play className="size-3.5" /> Open runner
              </Link>
              <button
                type="button"
                disabled={!readyToSave || saveConfig.isPending}
                onClick={() => handleGenerate()}
                className="flex items-center gap-2 px-5 py-2 rounded-full bg-foreground text-background font-medium text-sm disabled:opacity-40 hover:opacity-90 transition-opacity"
              >
                {saveConfig.isPending ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Zap className="size-3.5" />
                )}
                {saveConfig.isPending ? "Saving…" : "Save config"}
              </button>
            </div>
          </div>

          {/* Saved config preview — appears after save */}
          {savedConfigId && (
            <SavedConfigPreview configId={savedConfigId} onDismiss={() => setSavedConfigId(null)} />
          )}

          {/* Vision-only */}
          {configId && (
            <VisionOnly section="config.experimentSpec">
              <ExperimentSpecPanel configId={configId} />
            </VisionOnly>
          )}
          <VisionOnly section="config.personasEditor">
            <Panel className="p-5 space-y-5">
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

  // -------------------------------------------------------------------------
  // Non-workspace (demo) layout — init wizard
  // -------------------------------------------------------------------------
  const steps = wizard?.steps ?? [
    { id: "target", title: "Target URL", description: "Production or staging surface" },
    { id: "auth", title: "Auth", description: "Optional credentials via env" },
    { id: "journeys", title: "Journeys", description: "Persona × path matrix" },
    { id: "review", title: "Review", description: "Preflight & run" },
  ];
  const dogfoodHint =
    (wizard as unknown as { dogfood?: { hint?: string } } | undefined)?.dogfood?.hint ??
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
            journeys for /, /runs, /compare, /config, /runner.
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
            PII redaction in scorecards
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
            <legend className="text-xs text-muted-foreground">Viewport profiles</legend>
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

        <ProductIntelligencePanel
          live={!!live}
          targetUrl={targetUrl}
          productName={productName}
          configId={workspaceConfigId}
          onModelReady={handleProductModelReady}
          onCredsChange={handleCredsChange}
        />

        <PersonaStudioPanel
          live={!!live}
          targetUrl={targetUrl}
          productName={productName}
          configId={workspaceConfigId ?? undefined}
          productModel={productModel}
          personaLens={personaLens}
          onPersonaLensChange={setPersonaLens}
          personas={personas}
          onAddPersona={(p) =>
            setPersonas((prev) => (prev.some((x) => x.id === p.id) ? prev : [...prev, p]))
          }
          onRemovePersona={(id) => setPersonas((prev) => prev.filter((p) => p.id !== id))}
        />

        <JourneyDiscoveryPanel
          live={!!live}
          configId={workspaceConfigId}
          productModel={productModel}
          personas={personasForDiscovery}
        />

        <JourneyDraftPanel live={!!live} targetUrl={targetUrl} />

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
                +{hiddenConfigCount} more generated configs in artifacts.
              </div>
            )}
          </Panel>
        )}

        <Panel className="p-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="font-medium">Generate & write YAML</div>
            <div className="text-sm text-muted-foreground mt-1">
              Saves to: <code className="text-xs font-mono">configs/[slug].yaml</code>
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
