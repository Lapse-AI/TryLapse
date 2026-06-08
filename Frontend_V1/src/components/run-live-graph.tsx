import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle, Clock, Zap } from "lucide-react";

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
  const passCount = journey.steps.filter(s => s.status === "pass").length;
  const failCount = journey.steps.filter(s => s.status === "fail").length;
  const doneCount = passCount + failCount;

  return (
    <div className={`flex items-start gap-2 py-1.5 px-2 rounded-md transition-colors ${
      isActive ? "bg-primary/5 border border-primary/20" : "hover:bg-surface-2/30"
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
  );
}

function PersonaColumn({ persona, progress }: { persona: PersonaProgress; progress: RunProgress }) {
  const isActive = progress.current_persona === persona.persona_id;
  const doneJourneys = persona.journeys.filter(j => j.status === "pass" || j.status === "fail").length;
  const failedJourneys = persona.journeys.filter(j => j.status === "fail").length;

  return (
    <div className={`flex-1 min-w-0 border rounded-lg overflow-hidden transition-all ${
      isActive ? "border-primary/40 shadow-sm" : "border-border"
    }`}>
      {/* Persona header */}
      <div className={`px-3 py-2 flex items-center gap-2 ${
        isActive ? "bg-primary/10" : "bg-surface-2/50"
      }`}>
        <StatusIcon status={persona.status} size={16} />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold truncate">{persona.persona_name}</div>
          <div className="text-[10px] text-muted-foreground">
            {doneJourneys}/{persona.journeys.length} journeys
            {failedJourneys > 0 && <span className="text-red-400 ml-1">· {failedJourneys} failed</span>}
          </div>
        </div>
      </div>

      {/* Journey list */}
      <div className="divide-y divide-border/50 max-h-[340px] overflow-y-auto">
        {persona.journeys.length === 0 ? (
          <div className="px-3 py-4 text-[11px] text-muted-foreground text-center">
            Waiting for journeys…
          </div>
        ) : (
          persona.journeys.map(journey => (
            <div key={journey.journey_id} className="px-1.5 py-0.5">
              <JourneyRow
                journey={journey}
                isActive={progress.current_journey === journey.journey_id && isActive}
              />
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
}: {
  runId?: string;
  pollingMs?: number;
  jobId?: string;
}) {
  const [progress, setProgress] = useState<RunProgress | null>(null);
  const [noProgress, setNoProgress] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const url = runId ? `/api/progress?runId=${runId}` : "/api/progress";
        const res = await fetch(url);
        if (!res.ok) {
          if (!cancelled) setNoProgress(true);
          return;
        }
        const data = await res.json();
        if (!cancelled) {
          setProgress(data);
          setNoProgress(false);
        }
      } catch {
        if (!cancelled) setNoProgress(true);
      }
    };

    poll();
    const interval = setInterval(poll, pollingMs);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [runId, pollingMs]);

  // Job running but no progress file yet (run just queued, or backend was old)
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
        {jobId && (
          <div className="text-[11px] text-muted-foreground font-mono">job: {jobId}</div>
        )}
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
  const elapsedStr = elapsedS > 60
    ? `${Math.floor(elapsedS / 60)}m ${elapsedS % 60}s`
    : `${elapsedS}s`;

  const totalJourneys = progress.total_journeys || progress.personas.reduce((a, p) => a + p.journeys.length, 0);
  const completedJourneys = progress.completed_journeys ||
    progress.personas.reduce((a, p) => a + p.journeys.filter(j => j.status === "pass" || j.status === "fail").length, 0);
  const pct = totalJourneys > 0 ? Math.round((completedJourneys / totalJourneys) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          {isDone
            ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            : <Loader2 className="w-4 h-4 animate-spin text-primary" />}
          <span className="text-sm font-medium">
            {PHASE_LABELS[progress.phase] ?? progress.phase}
          </span>
          {progress.product_name && (
            <span className="text-xs text-muted-foreground">· {progress.product_name}</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Zap className="w-3 h-3" />{elapsedStr}</span>
          {totalJourneys > 0 && (
            <span>{completedJourneys}/{totalJourneys} journeys</span>
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

      {/* Error */}
      {progress.error && (
        <div className="text-xs text-red-500 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
          {progress.error}
        </div>
      )}

      {/* Persona × Journey grid */}
      {progress.personas.length > 0 && (
        <div className="flex gap-3 overflow-x-auto pb-1">
          {progress.personas.map(persona => (
            <PersonaColumn key={persona.persona_id} persona={persona} progress={progress} />
          ))}
        </div>
      )}

      {/* Phase hint when no persona data yet */}
      {progress.personas.length === 0 && !isDone && (
        <div className="text-xs text-muted-foreground text-center py-6">
          {progress.phase === "crawling" ? "Crawling product pages…" : "Preparing journeys…"}
        </div>
      )}
    </div>
  );
}
