import { useState, useCallback, useEffect } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import {
  Map,
  Loader2,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Download,
  Search,
  Globe,
  Brain,
  ListChecks,
  CheckCircle2,
  AlertCircle,
  Play,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type PersonaDraft = { id: string; name: string; role: string; goals: string[] };
type DiscoveredJourney = Record<string, unknown>;

type Phase =
  | { kind: "idle" }
  | { kind: "crawling"; message: string }
  | { kind: "planning"; message: string }
  | { kind: "expanding"; done: number; total: number }
  | { kind: "done" }
  | { kind: "error"; message: string };

type PersonaResult = {
  personaId: string;
  phase: Phase;
  journeyNames: string[];
  journeys: DiscoveredJourney[];
  usagePattern?: Record<string, unknown>;
  painPoints?: unknown[];
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PhaseIndicator({ phase }: { phase: Phase }) {
  if (phase.kind === "idle") return null;

  if (phase.kind === "done")
    return (
      <div className="flex items-center gap-1.5 text-xs text-ready">
        <CheckCircle2 className="size-3.5" />
        Discovery complete
      </div>
    );

  if (phase.kind === "error")
    return (
      <div className="flex items-center gap-1.5 text-xs text-danger">
        <AlertCircle className="size-3.5" />
        {phase.message}
      </div>
    );

  const steps = [
    { key: "crawling", icon: Globe, label: "Crawling product" },
    { key: "planning", icon: Brain, label: "Building journey plan" },
    { key: "expanding", icon: ListChecks, label: "Expanding journeys" },
  ] as const;

  const currentIdx = steps.findIndex((s) => s.key === phase.kind);

  return (
    <div className="space-y-1.5 py-1">
      {steps.map((step, i) => {
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        const Icon = step.icon;
        return (
          <div
            key={step.key}
            className={`flex items-center gap-2 text-xs transition-all duration-300 ${
              isActive
                ? "text-foreground"
                : isDone
                  ? "text-muted-foreground/50"
                  : "text-muted-foreground/30"
            }`}
          >
            {isActive ? (
              <Loader2 className="size-3 animate-spin text-primary" />
            ) : isDone ? (
              <CheckCircle2 className="size-3 text-ready/60" />
            ) : (
              <div className="size-3 rounded-full border border-current opacity-30" />
            )}
            <Icon className="size-3" />
            <span>
              {isActive && phase.kind === "crawling" ? phase.message : null}
              {isActive && phase.kind === "planning" ? phase.message : null}
              {isActive && phase.kind === "expanding"
                ? `${step.label} (${phase.done}/${phase.total})`
                : null}
              {!isActive ? step.label : null}
            </span>
          </div>
        );
      })}
    </div>
  );
}

type StepDraft = { action: string; intent: string; url: string; description: string };

function JourneyRow({
  j,
  isNew,
  onUpdate,
}: {
  j: DiscoveredJourney;
  isNew?: boolean;
  onUpdate: (updated: DiscoveredJourney) => void;
}) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);

  // Edit drafts
  const [name, setName] = useState(String(j.name ?? ""));
  const [description, setDescription] = useState(String(j.description ?? ""));
  const [entryPoint, setEntryPoint] = useState(String(j.entry_point ?? ""));
  const [priority, setPriority] = useState(String(j.priority ?? "medium"));
  const [frequency, setFrequency] = useState(String(j.frequency ?? "weekly"));
  const [steps, setSteps] = useState<StepDraft[]>(() =>
    ((j.steps as Array<Record<string, string>>) ?? []).map((s) => ({
      action: s.action ?? "navigate",
      intent: s.intent ?? "",
      url: s.url ?? "",
      description: s.description ?? "",
    })),
  );

  const priorityTone =
    j.priority === "critical" ? "danger" : j.priority === "high" ? "warn" : "neutral";

  const saveEdit = () => {
    onUpdate({
      ...j,
      name,
      description,
      entry_point: entryPoint,
      priority,
      frequency,
      steps: steps.map((s) => ({
        action: s.action,
        ...(s.intent ? { intent: s.intent } : {}),
        ...(s.url ? { url: s.url } : {}),
        ...(s.description ? { description: s.description } : {}),
      })),
    });
    setEditing(false);
  };

  const cancelEdit = () => {
    setName(String(j.name ?? ""));
    setDescription(String(j.description ?? ""));
    setEntryPoint(String(j.entry_point ?? ""));
    setPriority(String(j.priority ?? "medium"));
    setFrequency(String(j.frequency ?? "weekly"));
    setSteps(
      ((j.steps as Array<Record<string, string>>) ?? []).map((s) => ({
        action: s.action ?? "navigate",
        intent: s.intent ?? "",
        url: s.url ?? "",
        description: s.description ?? "",
      })),
    );
    setEditing(false);
  };

  const addStep = () =>
    setSteps((prev) => [...prev, { action: "navigate", intent: "", url: "/", description: "" }]);

  const removeStep = (i: number) => setSteps((prev) => prev.filter((_, idx) => idx !== i));

  const updateStep = (i: number, field: keyof StepDraft, value: string) =>
    setSteps((prev) => prev.map((s, idx) => (idx === i ? { ...s, [field]: value } : s)));

  return (
    <div
      className={`border border-border rounded-lg overflow-hidden transition-all duration-500 ${
        isNew ? "animate-in slide-in-from-top-1 fade-in" : ""
      }`}
    >
      {/* Header row */}
      <div className="flex items-center gap-1 px-3 py-2.5">
        <button
          type="button"
          className="flex-1 flex items-center gap-2 flex-wrap text-left min-w-0"
          onClick={() => { if (!editing) setOpen(!open); }}
        >
          <span className="text-sm font-medium">{String(j.name ?? "")}</span>
          <Chip tone={priorityTone}>{String(j.priority ?? "medium")}</Chip>
          <Chip tone="neutral">{String(j.frequency ?? "")}</Chip>
          <span className="text-[11px] text-muted-foreground font-mono">
            {((j.steps as unknown[]) ?? []).length} steps
          </span>
          {j.entry_point != null && (
            <span className="text-[10px] font-mono text-primary/70">{String(j.entry_point)}</span>
          )}
        </button>
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setEditing(!editing); setOpen(true); }}
          className="shrink-0 text-[11px] px-2 py-1 rounded border border-border hover:bg-surface-2/50 text-muted-foreground hover:text-foreground"
        >
          {editing ? "cancel" : "Edit"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="shrink-0 text-muted-foreground ml-1"
        >
          {open ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
        </button>
      </div>

      {open && !editing && (
        <div className="px-3 pb-3 border-t border-border space-y-3 pt-2">
          <p className="text-[11px] text-muted-foreground">{String(j.description ?? "")}</p>
          {((j.steps as Array<Record<string, string>>) ?? []).length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] text-muted-foreground font-medium">Steps</div>
              {(j.steps as Array<Record<string, string>>).map((s, i) => (
                <div key={i} className="text-xs flex items-start gap-2">
                  <span className="text-[10px] font-mono text-muted-foreground/60 w-4 mt-0.5 shrink-0">{i + 1}</span>
                  <Chip tone="neutral">{s.action}</Chip>
                  <span className="text-muted-foreground flex-1">{s.description || s.intent || s.url || ""}</span>
                </div>
              ))}
            </div>
          )}
          {j.behavioral_intent != null && (
            <div>
              <div className="text-[11px] text-muted-foreground font-medium">Intent</div>
              <p className="text-xs text-muted-foreground mt-0.5">{String(j.behavioral_intent)}</p>
            </div>
          )}
          {Array.isArray(j.failure_signals) && (j.failure_signals as string[]).length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground font-medium">Watch for</div>
              <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5 mt-0.5">
                {(j.failure_signals as string[]).map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {open && editing && (
        <div className="px-3 pb-4 border-t border-border space-y-3 pt-3 bg-surface-2/20">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] text-muted-foreground">Name</label>
              <input className="mt-0.5 w-full text-sm bg-surface border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="text-[11px] text-muted-foreground">Entry point</label>
              <input className="mt-0.5 w-full text-sm font-mono bg-surface border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                value={entryPoint} onChange={(e) => setEntryPoint(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="text-[11px] text-muted-foreground">Description</label>
            <textarea className="mt-0.5 w-full text-sm bg-surface border border-border rounded px-2 py-1.5 min-h-[56px] focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex gap-3">
            <div>
              <label className="text-[11px] text-muted-foreground">Priority</label>
              <select className="mt-0.5 block text-xs bg-surface border border-border rounded px-2 py-1.5"
                value={priority} onChange={(e) => setPriority(e.target.value)}>
                {["critical","high","medium","low"].map((v) => <option key={v}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[11px] text-muted-foreground">Frequency</label>
              <select className="mt-0.5 block text-xs bg-surface border border-border rounded px-2 py-1.5"
                value={frequency} onChange={(e) => setFrequency(e.target.value)}>
                {["daily","weekly","occasional","onboarding-only"].map((v) => <option key={v}>{v}</option>)}
              </select>
            </div>
          </div>

          {/* Steps editor */}
          <div>
            <div className="text-[11px] text-muted-foreground font-medium mb-1.5">Steps</div>
            <div className="space-y-2">
              {steps.map((s, i) => (
                <div key={i} className="flex items-start gap-2 bg-surface rounded-lg border border-border p-2">
                  <span className="text-[10px] font-mono text-muted-foreground/60 w-4 mt-2 shrink-0">{i + 1}</span>
                  <select
                    className="text-xs bg-surface-2 border border-border rounded px-1.5 py-1 shrink-0"
                    value={s.action}
                    onChange={(e) => updateStep(i, "action", e.target.value)}
                  >
                    {["navigate","click","fill","wait","scroll","hover","select","press","assert_url_contains","explore","dismiss"].map((a) => (
                      <option key={a}>{a}</option>
                    ))}
                  </select>
                  <input
                    className="flex-1 text-xs bg-surface border border-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary/30"
                    placeholder={s.action === "navigate" ? "url e.g. /dashboard" : "intent / label"}
                    value={s.action === "navigate" ? s.url : s.intent}
                    onChange={(e) => updateStep(i, s.action === "navigate" ? "url" : "intent", e.target.value)}
                  />
                  <button type="button" onClick={() => removeStep(i)}
                    className="text-muted-foreground/50 hover:text-danger shrink-0 mt-0.5">
                    ×
                  </button>
                </div>
              ))}
            </div>
            <button type="button" onClick={addStep}
              className="mt-2 text-[11px] px-2.5 py-1 rounded border border-dashed border-border hover:bg-surface-2/50 text-muted-foreground">
              + Add step
            </button>
          </div>

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={saveEdit}
              className="text-xs px-4 py-1.5 rounded-md bg-primary text-primary-foreground font-medium">
              Save changes
            </button>
            <button type="button" onClick={cancelEdit}
              className="text-xs px-3 py-1.5 rounded-md border border-border text-muted-foreground">
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PersonaCard({
  persona,
  result,
  onDiscover,
  onImport,
  onUpdateJourney,
  configId,
  live,
}: {
  persona: PersonaDraft;
  result: PersonaResult;
  onDiscover: (p: PersonaDraft) => void;
  onImport: (p: PersonaDraft) => void;
  onUpdateJourney: (idx: number, updated: DiscoveredJourney) => void;
  configId?: string | null;
  live: boolean;
}) {
  const phase = result.phase;
  const [collapsed, setCollapsed] = useState(false);

  const isRunning = phase.kind !== "idle" && phase.kind !== "done" && phase.kind !== "error";
  const hasDone = phase.kind === "done";
  const journeyCount = result.journeys.length;

  // Auto-expand when journeys first arrive
  useEffect(() => {
    if (journeyCount > 0) setCollapsed(false);
  }, [journeyCount > 0]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Panel className="overflow-hidden">
      {/* Persona header */}
      <div className="p-4 border-b border-border flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-display font-semibold text-sm">{persona.name}</span>
            <Chip tone="neutral">{persona.role}</Chip>
            {hasDone && journeyCount > 0 && (
              <Chip tone="ready">{journeyCount} journeys</Chip>
            )}
            {result.usagePattern?.session_frequency != null && (
              <Chip tone="neutral">
                {String(result.usagePattern.session_frequency)}
              </Chip>
            )}
          </div>
          {persona.goals.length > 0 && (
            <p className="text-[11px] text-muted-foreground mt-1 truncate">
              {persona.goals.slice(0, 2).join(" · ")}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {hasDone && configId && journeyCount > 0 && (
            <button
              type="button"
              onClick={() => onImport(persona)}
              className="flex items-center gap-1 text-[11px] px-2.5 py-1.5 rounded border border-border hover:bg-surface-2/50"
            >
              <Download className="size-3" /> Import
            </button>
          )}
          <button
            type="button"
            disabled={isRunning || !live}
            onClick={() => onDiscover(persona)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-primary/10 text-primary border border-primary/20 hover:bg-primary/15 disabled:opacity-40 transition-all"
          >
            {isRunning ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <Search className="size-3" />
            )}
            {isRunning ? "Researching…" : hasDone ? "Re-research" : "Research journeys"}
          </button>
        </div>
      </div>

      {/* Phase progress */}
      {isRunning && (
        <div className="px-4 py-3 border-b border-border bg-surface-2/30">
          <PhaseIndicator phase={phase} />
          {/* Journey name preview as they appear */}
          {result.journeyNames.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {result.journeyNames.map((name, i) => (
                <span
                  key={i}
                  className={`text-[10px] px-1.5 py-0.5 rounded border transition-all duration-300 ${
                    i < result.journeys.length
                      ? "bg-ready/10 border-ready/30 text-ready"
                      : "bg-surface border-border text-muted-foreground/50"
                  }`}
                >
                  {name}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Journey list */}
      {result.journeys.length > 0 && (
        <>
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="w-full flex items-center justify-between px-4 py-2 border-t border-border bg-surface-2/20 hover:bg-surface-2/50 transition-colors"
          >
            <span className="text-[11px] font-medium text-muted-foreground">
              {journeyCount} {journeyCount === 1 ? "journey" : "journeys"}
            </span>
            {collapsed ? <ChevronDown className="size-3.5 text-muted-foreground" /> : <ChevronUp className="size-3.5 text-muted-foreground" />}
          </button>
          {!collapsed && (
            <div className="p-4 space-y-2">
              {result.journeys.map((j, i) => (
                <JourneyRow
                  key={String(j.id ?? i)}
                  j={j}
                  isNew={isRunning && i === result.journeys.length - 1}
                  onUpdate={(updated) => onUpdateJourney(i, updated)}
                />
              ))}
              {Array.isArray(result.painPoints) && result.painPoints.length > 0 && (
                <div className="border border-warn/30 rounded-lg p-3 mt-1">
                  <div className="text-[11px] text-muted-foreground font-medium mb-1">
                    Anticipated pain points
                  </div>
                  {(result.painPoints as Array<Record<string, string>>).map((pp, i) => (
                    <div key={i} className="text-xs flex items-center gap-2 mt-1">
                      <Chip tone={pp.severity === "critical" ? "danger" : "warn"}>{pp.severity}</Chip>
                      <span>{pp.area}: {pp.concern}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Idle empty state */}
      {phase.kind === "idle" && result.journeys.length === 0 && (
        <div className="p-6 text-center text-xs text-muted-foreground">
          {live
            ? "Click Research journeys to crawl the product and discover real user paths."
            : "Start rehearse serve to enable journey discovery."}
        </div>
      )}
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

type Props = {
  live: boolean;
  personas: PersonaDraft[];
  configId?: string | null;
  productModel?: Record<string, unknown> | null;
};

export function JourneyDiscoveryPanel({ live, personas, configId, productModel }: Props) {
  const [results, setResults] = useState<Record<string, PersonaResult>>({});
  const [importingId, setImportingId] = useState<string | null>(null);

  const initResult = useCallback(
    (persona: PersonaDraft): PersonaResult =>
      results[persona.id] ?? {
        personaId: persona.id,
        phase: { kind: "idle" },
        journeyNames: [],
        journeys: [],
      },
    [results],
  );

  const patchResult = useCallback((personaId: string, patch: Partial<PersonaResult>) => {
    setResults((prev) => {
      const base: PersonaResult = prev[personaId] ?? {
        personaId,
        phase: { kind: "idle" },
        journeyNames: [],
        journeys: [],
      };
      return { ...prev, [personaId]: { ...base, ...patch } };
    });
  }, []);

  const discoverOne = useCallback(
    async (persona: PersonaDraft) => {
      if (!live) { toast.error("Start rehearse serve first"); return; }

      patchResult(persona.id, {
        phase: { kind: "crawling", message: "Crawling product with auth…" },
        journeyNames: [],
        journeys: [],
      });

      try {
        const stream = api.discoverJourneysForPersonaStream(persona, configId, productModel);
        for await (const ev of stream) {
          switch (ev.type) {
            case "phase1_start":
              patchResult(persona.id, {
                phase: { kind: "planning", message: "Generating journey plan from crawl data…" },
              });
              break;
            case "phase1_done":
              patchResult(persona.id, {
                phase: { kind: "expanding", done: 0, total: (ev.count as number) ?? 0 },
                journeyNames: (ev.names as string[]) ?? [],
                usagePattern: (ev.usage_pattern as Record<string, unknown>) ?? undefined,
              });
              break;
            case "journey_ready":
              setResults((prev) => {
                const cur = prev[persona.id] ?? { personaId: persona.id, phase: { kind: "expanding", done: 0, total: 0 }, journeyNames: [], journeys: [] };
                const newJourneys = [...cur.journeys, ev.journey as DiscoveredJourney];
                const total = cur.phase.kind === "expanding" ? cur.phase.total : newJourneys.length;
                return {
                  ...prev,
                  [persona.id]: {
                    ...cur,
                    journeys: newJourneys,
                    phase: { kind: "expanding", done: newJourneys.length, total },
                  },
                };
              });
              break;
            case "done":
              patchResult(persona.id, { phase: { kind: "done" } });
              break;
          }
        }
        patchResult(persona.id, { phase: { kind: "done" } });
        toast.success(`Journeys discovered for ${persona.name}`);
      } catch (e) {
        patchResult(persona.id, {
          phase: { kind: "error", message: e instanceof Error ? e.message : "Discovery failed" },
        });
        toast.error(`Discovery failed for ${persona.name}`);
      }
    },
    [live, configId, productModel, patchResult],
  );

  const discoverAll = useCallback(() => {
    if (!live) { toast.error("Start rehearse serve first"); return; }
    if (personas.length === 0) { toast.error("Add personas first"); return; }
    for (const p of personas) void discoverOne(p);
  }, [live, personas, discoverOne]);

  const importOne = useCallback(
    async (persona: PersonaDraft) => {
      if (!configId) { toast.error("No config ID — workspace config not found"); return; }
      const r = results[persona.id];
      if (!r?.journeys.length) { toast.error("No journeys to import"); return; }
      setImportingId(persona.id);
      try {
        // Tag each journey with the persona it was discovered for
        const tagged = r.journeys.map((j) => ({ ...j, persona_id: persona.id }));
        const res = await api.importJourneysToConfig(configId, tagged);
        toast.success(`Imported ${res.added} journeys for ${persona.name}`);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Import failed");
      } finally {
        setImportingId(null);
      }
    },
    [configId, results],
  );

  const importAll = useCallback(async () => {
    if (!configId) { toast.error("No config ID"); return; }
    // Tag each journey with the persona it was discovered for
    const allJourneys = Object.entries(results).flatMap(([personaId, r]) =>
      r.journeys.map((j) => ({ ...j, persona_id: personaId }))
    );
    if (!allJourneys.length) { toast.error("No journeys to import"); return; }
    setImportingId("__all__");
    try {
      const res = await api.importJourneysToConfig(configId, allJourneys);
      toast.success(`Imported ${res.added} journeys into config`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImportingId(null);
    }
  }, [configId, results]);

  const totalJourneys = Object.values(results).reduce((n, r) => n + r.journeys.length, 0);
  const anyRunning = Object.values(results).some(
    (r) => r.phase.kind !== "idle" && r.phase.kind !== "done" && r.phase.kind !== "error",
  );

  return (
    <div className="space-y-3">
      {/* Header bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Map className="size-4 text-primary" />
          <span className="font-display font-semibold text-sm">Journey discovery</span>
          <Chip tone="violet">crawl + AI</Chip>
          {totalJourneys > 0 && <Chip tone="ready">{totalJourneys} journeys total</Chip>}
        </div>
        <div className="flex items-center gap-2">
          {totalJourneys > 0 && configId && (
            <button
              type="button"
              disabled={importingId === "__all__"}
              onClick={() => void importAll()}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2/30 disabled:opacity-40"
            >
              {importingId === "__all__" ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Download className="size-3.5" />
              )}
              Import all to config
            </button>
          )}
          <button
            type="button"
            disabled={anyRunning || personas.length === 0 || !live}
            onClick={discoverAll}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-40"
          >
            {anyRunning ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Sparkles className="size-3.5" />
            )}
            {anyRunning ? "Researching…" : "Research all personas"}
          </button>
        </div>
      </div>

      {/* What the crawler uses */}
      {productModel && (
        <div className="rounded-lg border border-border bg-surface-2/30 px-3 py-2 text-[11px] text-muted-foreground flex flex-wrap gap-3">
          <span className="flex items-center gap-1">
            <Globe className="size-3" /> Deep crawls with auth + vision
          </span>
          <span className="flex items-center gap-1">
            <Brain className="size-3" /> Persona-aware journey planning
          </span>
          <span className="flex items-center gap-1">
            <ListChecks className="size-3" /> Exact buttons &amp; URLs from DOM
          </span>
          {productModel.targetUrl != null && (
            <span className="font-mono text-primary/70">{String(productModel.targetUrl)}</span>
          )}
        </div>
      )}

      {personas.length === 0 ? (
        <Panel className="p-8 text-center text-sm text-muted-foreground">
          <Map className="size-8 mx-auto opacity-20 mb-2" />
          Add personas first, then research their journeys.
        </Panel>
      ) : (
        <div className="space-y-3">
          {personas.map((persona) => (
            <PersonaCard
              key={persona.id}
              persona={persona}
              result={initResult(persona)}
              onDiscover={discoverOne}
              onImport={importOne}
              onUpdateJourney={(idx, updated) => {
                setResults((prev) => {
                  const cur = prev[persona.id];
                  if (!cur) return prev;
                  const journeys = [...cur.journeys];
                  journeys[idx] = updated;
                  return { ...prev, [persona.id]: { ...cur, journeys } };
                });
              }}
              configId={configId}
              live={live}
            />
          ))}
        </div>
      )}
    </div>
  );
}
