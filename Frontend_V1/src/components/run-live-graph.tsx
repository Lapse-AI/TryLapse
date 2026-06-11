import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle, Clock, Zap, ChevronDown, ChevronUp, Info, Pause, Play, Square } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { toast } from "sonner";

interface StepProgress {
  step_id: string;
  action: string;
  intent: string;
  status: "pending" | "running" | "pass" | "fail" | "skip";
  duration_ms: number;
  note: string;
}

interface JourneyProgress {
  journey_id: string;
  journey_name: string;
  persona_id: string;
  status: "pending" | "running" | "pass" | "fail";
  steps: StepProgress[];
  duration_ms: number;
}

interface PersonaProgress {
  persona_id: string;
  persona_name: string;
  status: "pending" | "running" | "done";
  journeys: JourneyProgress[];
}

interface RunProgress {
  run_id: string;
  product_name: string;
  target_url: string;
  phase: string;
  started_at: number;
  personas: PersonaProgress[];
  total_journeys: number;
  completed_journeys: number;
  total_steps: number;
  completed_steps: number;
  current_persona: string;
  current_journey: string;
  error: string;
}

const PHASE_LABELS: Record<string, string> = {
  starting: "Starting…",
  crawling: "Crawling product",
  discovering: "Discovering journeys",
  executing: "Executing journeys",
  analysing: "Analysing results",
  done: "Complete",
  failed: "Failed",
};

function StatusIcon({ status, size = 14 }: { status: string; size?: number }) {
  const s = `w-${size === 14 ? "3.5" : "4"} h-${size === 14 ? "3.5" : "4"}`;
  if (status === "running") return <Loader2 className={`${s} animate-spin text-primary`} />;
  if (status === "pass" || status === "done") return <CheckCircle2 className={`${s} text-emerald-500`} />;
  if (status === "fail") return <XCircle className={`${s} text-red-500`} />;
  return <Clock className={`${s} text-muted-foreground/40`} />;
}

function StepDot({ step }: { step: StepProgress }) {
  const color =
    step.status === "pass" ? "bg-emerald-500"
    : step.status === "fail" ? "bg-red-500"
    : step.status === "running" ? "bg-primary animate-pulse"
    : step.status === "skip" ? "bg-muted-foreground/30"
    : "bg-border";
  return (
    <div
      title={`${step.action}${step.intent ? `: ${step.intent}` : ""}${step.note ? ` — ${step.note}` : ""}`}
      className={`w-2 h-2 rounded-full flex-shrink-0 ${color} cursor-help`}
    />
  );
}

function JourneyRow({ journey, isActive }: { journey: JourneyProgress; isActive: boolean }) {
  const [open, setOpen] = useState(false);
  const passCount = journey.steps.filter(s => s.status === "pass").length;
  const failCount = journey.steps.filter(s => s.status === "fail").length;
  const doneCount = passCount + failCount;

  return (
    <div>
      <div
        className={`flex items-start gap-2 py-1.5 px-2 rounded-md transition-colors cursor-pointer ${
          isActive ? "bg-primary/5 border border-primary/20" : "hover:bg-surface-2/30"
        }`}
        onClick={() => setOpen(o => !o)}
      >
        <StatusIcon status={journey.status} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-medium truncate">{journey.journey_name}</span>
            <div className="flex items-center gap-1 shrink-0">
              {journey.duration_ms > 0 && (
                <span className="text-[10px] text-muted-foreground">
                  {(journey.duration_ms / 1000).toFixed(1)}s
                </span>
              )}
              {open ? <ChevronUp className="size-3 text-muted-foreground" /> : <ChevronDown className="size-3 text-muted-foreground" />}
            </div>
          </div>
          {!open && journey.steps.length > 0 && (
            <div className="flex items-center gap-0.5 mt-1 flex-wrap">
              {journey.steps.map(step => (
                <StepDot key={step.step_id} step={step} />
              ))}
              {doneCount > 0 && (
                <span className="text-[10px] text-muted-foreground ml-1">
                  {doneCount}/{journey.steps.length}
                  {failCount > 0 && <span className="text-red-400 ml-1">{failCount} fail</span>}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Expanded step detail */}
      {open && (
        <div className="mx-2 mb-1 rounded border border-border/60 bg-surface/60 divide-y divide-border/40 text-[11px]">
          {journey.steps.length === 0 ? (
            <div className="px-3 py-2 text-muted-foreground">No steps yet</div>
          ) : (
            journey.steps.map(step => (
              <div key={step.step_id} className="flex items-start gap-2 px-3 py-1.5">
                <div className={`mt-0.5 w-2 h-2 rounded-full shrink-0 ${
                  step.status === "pass" ? "bg-emerald-500"
                  : step.status === "fail" ? "bg-red-500"
                  : step.status === "running" ? "bg-primary animate-pulse"
                  : "bg-border"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-muted-foreground">{step.action}</span>
                    {step.intent && <span className="truncate text-foreground/80">{step.intent}</span>}
                    {step.duration_ms > 0 && (
                      <span className="ml-auto shrink-0 text-muted-foreground">
                        {(step.duration_ms / 1000).toFixed(2)}s
                      </span>
                    )}
                  </div>
                  {step.note && (
                    <div className="text-muted-foreground/70 mt-0.5 truncate">{step.note}</div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function PersonaDetail({ persona, progress, onClose }: {
  persona: PersonaProgress;
  progress: RunProgress;
  onClose: () => void;
}) {
  const passes = persona.journeys.filter(j => j.status === "pass").length;
  const fails  = persona.journeys.filter(j => j.status === "fail").length;
  const total  = persona.journeys.length;
  const totalSteps = persona.journeys.reduce((a, j) => a + j.steps.length, 0);
  const passedSteps = persona.journeys.reduce((a, j) => a + j.steps.filter(s => s.status === "pass").length, 0);
  const failedSteps = persona.journeys.reduce((a, j) => a + j.steps.filter(s => s.status === "fail").length, 0);
  const totalMs = persona.journeys.reduce((a, j) => a + j.duration_ms, 0);

  return (
    <div className="border border-primary/30 rounded-lg bg-surface/80 shadow-md">
      {/* Detail header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <StatusIcon status={persona.status} size={16} />
          <span className="text-sm font-semibold">{persona.persona_name}</span>
          <span className="text-xs text-muted-foreground font-mono">{persona.persona_id}</span>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xs px-2 py-0.5 rounded border border-border/60 hover:bg-surface-2">
          close
        </button>
      </div>

      {/* Stats row */}
      <div className="flex gap-6 px-4 py-2.5 border-b border-border text-xs">
        <div>
          <div className="text-muted-foreground">Journeys</div>
          <div className="font-mono font-medium">
            {passes}/{total}
            {fails > 0 && <span className="text-red-400 ml-1">· {fails} failed</span>}
          </div>
        </div>
        <div>
          <div className="text-muted-foreground">Steps</div>
          <div className="font-mono font-medium">
            {passedSteps}/{totalSteps}
            {failedSteps > 0 && <span className="text-red-400 ml-1">· {failedSteps} failed</span>}
          </div>
        </div>
        {totalMs > 0 && (
          <div>
            <div className="text-muted-foreground">Duration</div>
            <div className="font-mono font-medium">{(totalMs / 1000).toFixed(1)}s</div>
          </div>
        )}
        {progress.run_id && (
          <div className="ml-auto">
            <Link
              to="/runs/$runId"
              params={{ runId: progress.run_id }}
              className="text-primary hover:underline text-xs"
            >
              View full run →
            </Link>
          </div>
        )}
      </div>

      {/* Journey list with step expansion */}
      <div className="divide-y divide-border/40 max-h-64 overflow-y-auto">
        {persona.journeys.map(journey => (
          <div key={journey.journey_id} className="px-2 py-0.5">
            <JourneyRow
              journey={journey}
              isActive={progress.current_journey === journey.journey_id && progress.current_persona === persona.persona_id}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function PersonaColumn({ persona, progress, selected, onSelect }: {
  persona: PersonaProgress;
  progress: RunProgress;
  selected: boolean;
  onSelect: () => void;
}) {
  const isActive = progress.current_persona === persona.persona_id;
  const doneJourneys = persona.journeys.filter(j => j.status === "pass" || j.status === "fail").length;
  const failedJourneys = persona.journeys.filter(j => j.status === "fail").length;

  return (
    <div
      className={`flex-1 min-w-[150px] border rounded-lg overflow-hidden transition-all cursor-pointer ${
        selected
          ? "border-primary/60 shadow-md ring-1 ring-primary/20"
          : isActive
            ? "border-primary/40 shadow-sm"
            : "border-border hover:border-border/80 hover:shadow-sm"
      }`}
      onClick={onSelect}
      title="Click to expand details"
    >
      {/* Persona header */}
      <div className={`px-3 py-2 flex items-center gap-2 ${
        selected ? "bg-primary/15" : isActive ? "bg-primary/10" : "bg-surface-2/50"
      }`}>
        <StatusIcon status={persona.status} size={16} />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold leading-tight" title={persona.persona_name}>{persona.persona_name}</div>
          <div className="text-[10px] text-muted-foreground">
            {doneJourneys}/{persona.journeys.length} journeys
            {failedJourneys > 0 && <span className="text-red-400 ml-1">· {failedJourneys} failed</span>}
          </div>
        </div>
        {selected
          ? <ChevronUp className="size-3 text-primary shrink-0" />
          : <ChevronDown className="size-3 text-muted-foreground shrink-0" />
        }
      </div>

      {/* Journey list (collapsed view) */}
      <div className="divide-y divide-border/50 max-h-[340px] overflow-y-auto">
        {persona.journeys.length === 0 ? (
          <div className="px-3 py-4 text-[11px] text-muted-foreground text-center">
            Waiting for journeys…
          </div>
        ) : (
          persona.journeys.map(journey => (
            <div key={journey.journey_id} className="px-1.5 py-0.5">
              <div className={`flex items-start gap-2 py-1.5 px-2 rounded-md ${
                progress.current_journey === journey.journey_id && isActive
                  ? "bg-primary/5 border border-primary/20"
                  : ""
              }`}>
                <StatusIcon status={journey.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium truncate">{journey.journey_name}</span>
                    {journey.duration_ms > 0 && (
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        {(journey.duration_ms / 1000).toFixed(1)}s
                      </span>
                    )}
                  </div>
                  {journey.steps.length > 0 && (
                    <div className="flex items-center gap-0.5 mt-1 flex-wrap">
                      {journey.steps.slice(0, 12).map(step => (
                        <StepDot key={step.step_id} step={step} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function RunLiveGraph({
  runId,
  pollingMs = 2000,
  jobId,
  onRunIdDiscovered,
}: {
  runId?: string;
  pollingMs?: number;
  jobId?: string;
  onRunIdDiscovered?: (runId: string) => void;
}) {
  const [progress, setProgress] = useState<RunProgress | null>(null);
  const [noProgress, setNoProgress] = useState(false);
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);
  const [controlling, setControlling] = useState(false);

  const activeRunId = progress?.run_id ?? runId;

  async function sendSignal(signal: "pause" | "resume" | "stop") {
    if (!activeRunId) return;
    setControlling(true);
    try {
      const res = await fetch(`/api/runs/${encodeURIComponent(activeRunId)}/control`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ signal }),
      });
      if (res.ok) {
        if (signal === "pause") { setPaused(true); toast.success("Run paused"); }
        if (signal === "resume") { setPaused(false); toast.success("Run resumed"); }
        if (signal === "stop") { toast.success("Stop signal sent"); }
      } else {
        toast.error("Failed to send signal");
      }
    } catch {
      toast.error("Failed to reach server");
    } finally {
      setControlling(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const url = runId ? `/api/progress?runId=${runId}` : "/api/progress";
        const res = await fetch(url);
        if (!res.ok) { if (!cancelled) setNoProgress(true); return; }
        const data = await res.json();
        if (!cancelled) {
          setProgress(data);
          setNoProgress(false);
          if (data.run_id && onRunIdDiscovered) onRunIdDiscovered(data.run_id);
        }
      } catch {
        if (!cancelled) setNoProgress(true);
      }
    };
    poll();
    const interval = setInterval(poll, pollingMs);
    return () => { cancelled = true; clearInterval(interval); };
  }, [runId, pollingMs]);

  if (noProgress && !progress) {
    return (
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin text-primary" />
          <span>Crawling product — detailed step view begins when journeys start</span>
        </div>
        <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
          <div className="h-full w-1/3 bg-primary/50 rounded-full animate-pulse" />
        </div>
        {jobId && <div className="text-[11px] text-muted-foreground font-mono">job: {jobId}</div>}
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="flex items-center gap-2 p-2 text-sm text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        Waiting for progress data…
      </div>
    );
  }

  const isDone = progress.phase === "done" || progress.phase === "failed";
  const elapsedS = Math.floor(Date.now() / 1000 - progress.started_at);
  const elapsedStr = elapsedS > 60 ? `${Math.floor(elapsedS / 60)}m ${elapsedS % 60}s` : `${elapsedS}s`;
  const totalJourneys = progress.total_journeys || progress.personas.reduce((a, p) => a + p.journeys.length, 0);
  const completedJourneys = progress.completed_journeys ||
    progress.personas.reduce((a, p) => a + p.journeys.filter(j => j.status === "pass" || j.status === "fail").length, 0);
  const pct = totalJourneys > 0 ? Math.round((completedJourneys / totalJourneys) * 100) : 0;

  const browserPersonas = progress.personas.filter(p => p.journeys.some(j => j.steps.length > 0));
  const analysisOnlyCount = progress.personas.length - browserPersonas.length;
  const selectedPersona = selectedPersonaId
    ? progress.personas.find(p => p.persona_id === selectedPersonaId) ?? null
    : null;

  return (
    <div className="space-y-4">
      {/* Header with pause/stop controls */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          {isDone
            ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            : <Loader2 className="w-4 h-4 animate-spin text-primary" />}
          <span className="text-sm font-medium">{PHASE_LABELS[progress.phase] ?? progress.phase}</span>
          {progress.product_name && (
            <span className="text-xs text-muted-foreground">· {progress.product_name}</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><Zap className="w-3 h-3" />{elapsedStr}</span>
            {totalJourneys > 0 && <span>· {completedJourneys}/{totalJourneys} journeys</span>}
          </div>
          {/* Run controls — visible as soon as we have a run_id */}
          {activeRunId && !isDone && (
            <div className="flex items-center gap-1">
              {paused ? (
                <button
                  onClick={() => sendSignal("resume")}
                  disabled={controlling}
                  className="flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-emerald-500/40 text-emerald-500 hover:bg-emerald-500/10 disabled:opacity-40"
                >
                  <Play className="size-3" /> Resume
                </button>
              ) : (
                <button
                  onClick={() => sendSignal("pause")}
                  disabled={controlling}
                  className="flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-border text-muted-foreground hover:bg-surface-2 disabled:opacity-40"
                >
                  <Pause className="size-3" /> Pause
                </button>
              )}
              <button
                onClick={() => { if (confirm("Stop this run?")) sendSignal("stop"); }}
                disabled={controlling}
                className="flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-red-500/40 text-red-500 hover:bg-red-500/10 disabled:opacity-40"
              >
                <Square className="size-3" /> Stop
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {totalJourneys > 0 && (
        <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              progress.phase === "failed" ? "bg-red-500" : "bg-primary"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      {/* Analysis-only personas notice */}
      {analysisOnlyCount > 0 && (
        <div className="flex items-start gap-2 rounded-md border border-border/60 bg-surface-2/40 px-3 py-2 text-[11px] text-muted-foreground">
          <Info className="size-3.5 mt-0.5 shrink-0" />
          <span>
            <strong className="text-foreground">{browserPersonas.length === 0 ? progress.personas.length : browserPersonas.length}</strong> persona{browserPersonas.length === 1 ? "" : "s"} running browser journeys.{" "}
            {analysisOnlyCount} persona{analysisOnlyCount === 1 ? "" : "s"} are analysis-only (they review the same run, not separate browser sessions).{" "}
            Add <code className="font-mono bg-surface px-0.5 rounded">execute_all_personas_in_browser: true</code> to your config's <code className="font-mono bg-surface px-0.5 rounded">run:</code> section to browser-run all personas.
          </span>
        </div>
      )}

      {/* Error */}
      {progress.error && (
        <div className="text-xs text-red-500 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
          {progress.error}
        </div>
      )}

      {/* Persona columns — click any to expand detail below */}
      {progress.personas.length > 0 && (
        <>
          <div className="flex gap-3 overflow-x-auto pb-1">
            {progress.personas.map(persona => (
              <PersonaColumn
                key={persona.persona_id}
                persona={persona}
                progress={progress}
                selected={selectedPersonaId === persona.persona_id}
                onSelect={() =>
                  setSelectedPersonaId(id =>
                    id === persona.persona_id ? null : persona.persona_id
                  )
                }
              />
            ))}
          </div>

          {/* Expanded detail panel */}
          {selectedPersona && (
            <PersonaDetail
              persona={selectedPersona}
              progress={progress}
              onClose={() => setSelectedPersonaId(null)}
            />
          )}
        </>
      )}

      {progress.personas.length === 0 && !isDone && (
        <div className="text-xs text-muted-foreground text-center py-6">
          {progress.phase === "crawling" ? "Crawling product pages…" : "Preparing journeys…"}
        </div>
      )}
    </div>
  );
}
