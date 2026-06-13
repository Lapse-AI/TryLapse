/**
 * Step bifurcation tree: Run → Persona → Journey → Step
 * Shows the full execution hierarchy with pass/fail at every level.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, Clock, Loader2, AlertCircle } from "lucide-react";

interface Step {
  stepId: string;
  journeyId: string;
  journeyName: string;
  personaId: string;
  action: string;
  requestedUrl?: string;
  finalUrl?: string;
  outcome: string;
  durationMs: number;
  note?: string;
  errorType?: string;
  flaky?: boolean;
  consoleErrors?: string[];
  networkFailures?: string[];
  behavior?: { behavioral_verdict?: string; ux_concerns?: string[] };
}

interface Persona {
  id: string;
  name: string;
}

interface JourneyGroup {
  id: string;
  name: string;
  steps: Step[];
  pass: number;
  fail: number;
  total: number;
  durationMs: number;
}

interface PersonaGroup {
  persona: Persona;
  journeys: JourneyGroup[];
  pass: number;
  fail: number;
  total: number;
}

function outcomeColor(outcome: string): string {
  if (outcome === "pass") return "text-emerald-500";
  if (outcome === "fail") return "text-red-500";
  if (outcome === "skipped") return "text-muted-foreground/50";
  return "text-muted-foreground/40";
}

function OutcomeIcon({ outcome, size = 14 }: { outcome: string; size?: number }) {
  const cls = `shrink-0 ${size === 14 ? "size-3.5" : "size-4"}`;
  if (outcome === "pass") return <CheckCircle2 className={`${cls} text-emerald-500`} />;
  if (outcome === "fail") return <XCircle className={`${cls} text-red-500`} />;
  if (outcome === "skipped") return <Clock className={`${cls} text-muted-foreground/30`} />;
  return <Clock className={`${cls} text-muted-foreground/30`} />;
}

function PassRateBar({ pass, total }: { pass: number; total: number }) {
  const pct = total > 0 ? Math.round((pass / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
      <div className="w-16 h-1 bg-surface-2 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span>{pass}/{total}</span>
    </div>
  );
}

function StepRow({ step, index }: { step: Step; index: number }) {
  const [open, setOpen] = useState(false);
  const hasDetail = !!(step.note || (step.consoleErrors?.length) || (step.networkFailures?.length));

  return (
    <div className={`border-b border-border/30 last:border-0 ${step.flaky ? "bg-warn/5" : ""}`}>
      <div
        className={`flex items-start gap-2 px-4 py-1.5 text-[11px] ${hasDetail ? "cursor-pointer hover:bg-surface-2/40" : ""}`}
        onClick={() => hasDetail && setOpen(o => !o)}
      >
        <span className="text-muted-foreground/40 font-mono w-4 shrink-0 mt-0.5">{index + 1}</span>
        <OutcomeIcon outcome={step.outcome} size={14} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`font-mono font-medium ${outcomeColor(step.outcome)}`}>{step.action}</span>
            {step.requestedUrl && (
              <span className="text-muted-foreground truncate max-w-[200px]">{step.requestedUrl}</span>
            )}
            {step.flaky && <span className="text-warn text-[10px] border border-warn/30 rounded px-1">flaky</span>}
            {step.errorType && (
              <span className="text-red-400/80 text-[10px]">{step.errorType}</span>
            )}
          </div>
          {step.note && !open && (
            <div className="text-muted-foreground/60 truncate mt-0.5 max-w-[400px]">{step.note}</div>
          )}
        </div>
        <span className="text-muted-foreground/50 shrink-0 font-mono">
          {step.durationMs > 0 ? `${(step.durationMs / 1000).toFixed(2)}s` : "—"}
        </span>
        {hasDetail && (
          open ? <ChevronDown className="size-3 text-muted-foreground shrink-0 mt-0.5" />
                : <ChevronRight className="size-3 text-muted-foreground shrink-0 mt-0.5" />
        )}
      </div>

      {open && (
        <div className="mx-10 mb-2 rounded border border-border/60 bg-surface/40 px-3 py-2 text-[11px] space-y-1.5">
          {step.note && (
            <div>
              <span className="text-muted-foreground font-medium">Note: </span>
              <span className="text-foreground/80 font-mono whitespace-pre-wrap">{step.note}</span>
            </div>
          )}
          {step.finalUrl && step.finalUrl !== step.requestedUrl && (
            <div>
              <span className="text-muted-foreground font-medium">Final URL: </span>
              <span className="font-mono text-muted-foreground">{step.finalUrl}</span>
            </div>
          )}
          {(step.consoleErrors?.length ?? 0) > 0 && (
            <div>
              <span className="text-red-400 font-medium">Console errors: </span>
              {step.consoleErrors!.map((e, i) => (
                <div key={i} className="font-mono text-red-400/80 ml-2">{e}</div>
              ))}
            </div>
          )}
          {(step.networkFailures?.length ?? 0) > 0 && (
            <div>
              <span className="text-warn font-medium">Network failures: </span>
              {step.networkFailures!.map((e, i) => (
                <div key={i} className="font-mono text-warn/80 ml-2">{e}</div>
              ))}
            </div>
          )}
          {step.behavior?.ux_concerns?.length && (
            <div>
              <span className="text-muted-foreground font-medium">UX concerns: </span>
              {step.behavior.ux_concerns.map((c, i) => <div key={i} className="ml-2">{c}</div>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function JourneyBlock({ journey, defaultOpen }: { journey: JourneyGroup; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const grade = journey.fail === 0 && journey.pass > 0 ? "pass"
    : journey.fail > 0 && journey.pass === 0 ? "fail"
    : journey.fail > 0 ? "partial" : "pending";
  const gradeColor = grade === "pass" ? "text-emerald-500" : grade === "fail" ? "text-red-500" : grade === "partial" ? "text-warn" : "text-muted-foreground/40";

  return (
    <div className={`border border-border/60 rounded-md overflow-hidden ${grade === "fail" ? "border-red-500/20" : grade === "partial" ? "border-warn/20" : ""}`}>
      <button
        className={`w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-surface-2/40 transition-colors ${open ? "bg-surface-2/20" : ""}`}
        onClick={() => setOpen(o => !o)}
      >
        {open ? <ChevronDown className="size-3 shrink-0 text-muted-foreground" />
               : <ChevronRight className="size-3 shrink-0 text-muted-foreground" />}
        <span className={`font-medium ${gradeColor}`}>{journey.name}</span>
        <span className="text-muted-foreground/50 text-[10px]">{journey.id}</span>
        <div className="ml-auto flex items-center gap-3">
          <PassRateBar pass={journey.pass} total={journey.total} />
          {journey.durationMs > 0 && (
            <span className="text-muted-foreground/50 font-mono text-[10px]">
              {(journey.durationMs / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      </button>

      {open && (
        <div className="divide-y divide-border/20 bg-surface/30">
          {journey.steps.length === 0 ? (
            <div className="px-10 py-3 text-[11px] text-muted-foreground">No steps recorded</div>
          ) : (
            journey.steps.map((step, i) => <StepRow key={step.stepId} step={step} index={i} />)
          )}
        </div>
      )}
    </div>
  );
}

function PersonaSection({ group }: { group: PersonaGroup }) {
  const [open, setOpen] = useState(true);
  const grade = group.total === 0 ? "pending"
    : group.fail === 0 ? "pass"
    : group.pass === 0 ? "fail" : "partial";

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-semibold hover:bg-surface-2/40 transition-colors ${open ? "border-b border-border/60 bg-surface-2/20" : ""}`}
        onClick={() => setOpen(o => !o)}
      >
        {open ? <ChevronDown className="size-4 text-muted-foreground" /> : <ChevronRight className="size-4 text-muted-foreground" />}
        {grade === "pass" ? <CheckCircle2 className="size-4 text-emerald-500" />
          : grade === "fail" ? <XCircle className="size-4 text-red-500" />
          : grade === "partial" ? <AlertCircle className="size-4 text-warn" />
          : <Clock className="size-4 text-muted-foreground/40" />}
        <span>{group.persona.name}</span>
        <span className="text-xs font-normal text-muted-foreground font-mono">{group.persona.id}</span>
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-muted-foreground">
            {group.journeys.length} journey{group.journeys.length !== 1 ? "s" : ""}
          </span>
          {group.total > 0 && <PassRateBar pass={group.pass} total={group.total} />}
        </div>
      </button>

      {open && (
        <div className="p-3 space-y-2">
          {group.journeys.length === 0 ? (
            <div className="text-xs text-muted-foreground py-4 text-center">
              No browser journeys — this persona was analysis-only for this run.
            </div>
          ) : (
            group.journeys.map((j, i) => (
              <JourneyBlock key={j.id} journey={j} defaultOpen={i === 0 && group.journeys.length === 1} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

interface Props {
  steps: Step[];
  personas: Persona[];
  journeys: { id: string; name: string }[];
}

export function JourneyStepTree({ steps, personas, journeys }: Props) {
  if (steps.length === 0 && personas.length === 0) {
    return (
      <div className="py-16 text-center text-sm text-muted-foreground">
        No step execution data for this run. This happens when journey execution was skipped
        or all journeys failed before any steps could complete.
      </div>
    );
  }

  // Group steps: persona → journey → steps
  const personaMap = new Map<string, PersonaGroup>();

  // Seed from config (ensure all personas appear even with 0 steps)
  for (const p of personas) {
    personaMap.set(p.id, { persona: p, journeys: [], pass: 0, fail: 0, total: 0 });
  }

  // Group steps by persona + journey
  const journeyMap = new Map<string, Map<string, Step[]>>();
  for (const step of steps) {
    if (!journeyMap.has(step.personaId)) journeyMap.set(step.personaId, new Map());
    const jm = journeyMap.get(step.personaId)!;
    const key = step.journeyId;
    if (!jm.has(key)) jm.set(key, []);
    jm.get(key)!.push(step);
  }

  // Build persona groups
  for (const [pid, jm] of journeyMap) {
    const persona = personas.find(p => p.id === pid) ?? { id: pid, name: pid };
    const group: PersonaGroup = personaMap.get(pid) ?? { persona, journeys: [], pass: 0, fail: 0, total: 0 };
    personaMap.set(pid, group);

    for (const [jid, jSteps] of jm) {
      const jName = jSteps[0]?.journeyName ?? journeys.find(j => j.id === jid)?.name ?? jid;
      const pass = jSteps.filter(s => s.outcome === "pass").length;
      const fail = jSteps.filter(s => s.outcome === "fail").length;
      const durationMs = jSteps.reduce((a, s) => a + (s.durationMs || 0), 0);
      group.journeys.push({ id: jid, name: jName, steps: jSteps, pass, fail, total: jSteps.length, durationMs });
      group.pass += pass;
      group.fail += fail;
      group.total += jSteps.length;
    }
  }

  // Personas with steps first, then analysis-only
  const sorted = Array.from(personaMap.values()).sort((a, b) => b.total - a.total);

  return (
    <div className="space-y-3">
      <div className="text-xs text-muted-foreground">
        {steps.length} steps across {new Set(steps.map(s => s.journeyId)).size} journeys and{" "}
        {new Set(steps.map(s => s.personaId)).size} personas.
        Click a persona or journey to expand. Click a step to see details.
      </div>
      {sorted.map(group => (
        <PersonaSection key={group.persona.id} group={group} />
      ))}
    </div>
  );
}
