import { useEffect, useRef, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import {
  GitCompare,
  CheckCircle2,
  XCircle,
  Loader2,
  FlaskConical,
  ArrowRight,
  Send,
  Sparkles,
} from "lucide-react";

export const Route = createFileRoute("/experiment/$jobId")({
  head: () => ({ meta: [{ title: "Variant experiment — Launch Rehearsal" }] }),
  component: ExperimentReport,
});

type VariantJob = Awaited<ReturnType<typeof api.getVariantJob>>;
type ExperimentReport = Awaited<ReturnType<typeof api.getExperimentReport>>;
type ChatTurn = { role: string; content: string; at?: string };

const PHASE_LABELS: Record<string, string> = {
  queued: "Queued",
  "running-A": "Running config A (control)…",
  "running-B": "Running config B (variant)…",
  comparing: "Generating comparison report…",
  done: "Done",
  failed: "Failed",
};

const GRADE_COLORS: Record<string, string> = {
  pass: "text-ready",
  partial: "text-warn",
  fail: "text-danger",
  "—": "text-muted-foreground",
};

function PhaseBar({ phase }: { phase: string }) {
  const phases = ["running-A", "running-B", "comparing", "done"];
  const idx = phases.indexOf(phase);
  return (
    <div className="flex items-center gap-1 text-xs flex-wrap">
      {phases.map((p, i) => (
        <div key={p} className="flex items-center gap-1">
          <div
            className={[
              "px-2 py-0.5 rounded-full",
              i < idx
                ? "bg-ready/20 text-ready"
                : i === idx
                  ? "bg-primary/20 text-primary font-medium"
                  : "bg-surface-2 text-muted-foreground",
            ].join(" ")}
          >
            {p === "running-A"
              ? "A"
              : p === "running-B"
                ? "B"
                : p === "comparing"
                  ? "compare"
                  : "done"}
          </div>
          {i < phases.length - 1 && <ArrowRight className="size-3 text-muted-foreground" />}
        </div>
      ))}
    </div>
  );
}

function VerdictChip({ verdict }: { verdict: string }) {
  const tone = verdict === "held" ? "ready" : verdict === "regressed" ? "danger" : "warn";
  const label =
    verdict === "held"
      ? "Hypothesis held"
      : verdict === "regressed"
        ? "Hypothesis regressed"
        : "Inconclusive";
  return <Chip tone={tone}>{label}</Chip>;
}

function ReadinessBadge({ runId }: { runId: string | null }) {
  const [readiness, setReadiness] = useState<number | null>(null);
  const [band, setBand] = useState<string | null>(null);
  useEffect(() => {
    if (!runId) return;
    api
      .summaries()
      .then((list) => {
        const r = list.find(
          (s) => s.run_id === runId || (s as Record<string, string>).id === runId,
        );
        if (r) {
          setReadiness((r as Record<string, number>).readiness ?? null);
          setBand((r as Record<string, string>).readinessBand ?? null);
        }
      })
      .catch(() => {});
  }, [runId]);
  if (!runId) return <Chip tone="neutral">—</Chip>;
  if (readiness === null) return <Chip tone="neutral">loading…</Chip>;
  const tone = band === "Green" ? "ready" : band === "Red" ? "danger" : "warn";
  return (
    <Chip tone={tone}>
      {band} {readiness}
    </Chip>
  );
}

function ExperimentChatPanel({ jobId, live }: { jobId: string; live: boolean }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!live) return;
    api
      .getExperimentChat(jobId)
      .then((t) => setTurns(t.turns))
      .catch(() => {});
  }, [jobId, live]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || sending || !live) return;
    setInput("");
    setSending(true);
    setTurns((prev) => [...prev, { role: "user", content: msg }]);
    try {
      const res = await api.sendExperimentChat(jobId, msg);
      setTurns(res.turns);
    } catch {
      setTurns((prev) => [...prev, { role: "assistant", content: "Error — try again." }]);
    } finally {
      setSending(false);
    }
  };

  const SUGGESTED = [
    "Did the hypothesis hold for evaluators?",
    "What were the biggest improvements in variant B?",
    "Which persona benefited most?",
    "What new issues appeared in the variant?",
  ];

  return (
    <Panel className="overflow-hidden">
      <div className="p-4 border-b border-border flex items-center gap-2">
        <Sparkles className="size-4 text-violet" />
        <span className="font-display font-semibold text-sm">Experiment chat</span>
        <Chip tone="violet">L3-PRED-05</Chip>
        {!live && <Chip tone="warn">API offline</Chip>}
      </div>

      <div className="min-h-[180px] max-h-[320px] overflow-y-auto p-4 space-y-3">
        {turns.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Ask about this experiment:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => setInput(q)}
                  className="text-xs px-2 py-1 rounded-md border border-border hover:bg-surface-2"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={[
                "max-w-[80%] rounded-xl px-3 py-2 text-sm",
                t.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-surface-2 border border-border",
              ].join(" ")}
            >
              {t.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-surface-2 border border-border rounded-xl px-3 py-2">
              <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-border flex gap-2">
        <input
          className="flex-1 text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
          placeholder={live ? "Ask about the experiment…" : "Start rehearse serve to chat"}
          value={input}
          disabled={!live || sending}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <button
          type="button"
          disabled={!live || sending || !input.trim()}
          onClick={() => void send()}
          className="p-2 rounded-md bg-primary text-primary-foreground disabled:opacity-40"
        >
          <Send className="size-4" />
        </button>
      </div>
    </Panel>
  );
}

export default function ExperimentReport() {
  const { jobId } = Route.useParams();
  const [job, setJob] = useState<VariantJob | null>(null);
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [live, setLive] = useState(false);

  useEffect(() => {
    api
      .summaries()
      .then(() => setLive(true))
      .catch(() => setLive(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const data = await api.getVariantJob(jobId);
        if (!cancelled) {
          setJob(data);
          if (data.status === "done" || data.status === "failed") return;
          setTimeout(poll, 2000);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      }
    };
    void poll();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  useEffect(() => {
    if (job?.status !== "done") return;
    api
      .getExperimentReport(jobId)
      .then(setReport)
      .catch(() => {});
  }, [job?.status, jobId]);

  if (error) {
    return (
      <div className="p-8">
        <PageHeader eyebrow="experiment" title="Variant experiment" />
        <Panel className="p-6 text-danger">{error}</Panel>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="p-8">
        <PageHeader eyebrow="experiment" title="Variant experiment" />
        <Panel className="p-6 flex items-center gap-2 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Loading…
        </Panel>
      </div>
    );
  }

  const isRunning = job.status === "queued" || job.status === "running";
  const configAName = job.configA.split("/").pop()?.replace(".yaml", "") ?? job.configA;
  const configBName = job.configB.split("/").pop()?.replace(".yaml", "") ?? job.configB;
  const narrative = (job.diffNarrative ??
    (job.diff as Record<string, unknown> | undefined)?.narrative) as
    | Record<string, string>
    | null
    | undefined;
  const newIssues =
    ((job.diff as Record<string, unknown> | undefined)?.newIssues as unknown[]) ?? [];
  const resolvedIssues =
    ((job.diff as Record<string, unknown> | undefined)?.resolvedIssues as unknown[]) ?? [];

  return (
    <div>
      <PageHeader
        eyebrow="experiment"
        title="Variant experiment report"
        description={job.hypothesis || "Side-by-side rehearsal — control vs variant"}
      />
      <div className="p-8 max-w-[900px] space-y-6">
        {/* Status */}
        <Panel className="p-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <FlaskConical className="size-4 text-primary" />
              <span className="font-display font-semibold text-sm font-mono">{jobId}</span>
              <Chip
                tone={job.status === "done" ? "ready" : job.status === "failed" ? "danger" : "info"}
              >
                {job.status}
              </Chip>
              {report && <VerdictChip verdict={report.hypothesisVerdict} />}
              {report && (
                <Chip
                  tone={
                    report.readinessDelta > 0
                      ? "ready"
                      : report.readinessDelta < 0
                        ? "danger"
                        : "neutral"
                  }
                >
                  {report.readinessDelta > 0 ? "+" : ""}
                  {report.readinessDelta} pts readiness
                </Chip>
              )}
            </div>
            {isRunning && <Loader2 className="size-4 animate-spin text-primary" />}
            {job.status === "done" && <CheckCircle2 className="size-4 text-ready" />}
            {job.status === "failed" && <XCircle className="size-4 text-danger" />}
          </div>
          <PhaseBar phase={job.phase} />
          {job.error && (
            <div className="text-xs text-danger font-mono bg-danger/5 border border-danger/20 rounded-md p-3">
              {job.error}
            </div>
          )}
        </Panel>

        {/* Hypothesis */}
        {(job.hypothesis || job.userGoal) && (
          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground">Experiment spec</div>
            {job.hypothesis && (
              <div>
                <span className="text-xs font-medium text-muted-foreground">Hypothesis: </span>
                <span className="text-sm">{job.hypothesis}</span>
              </div>
            )}
            {job.userGoal && (
              <div>
                <span className="text-xs font-medium text-muted-foreground">User goal: </span>
                <span className="text-sm">{job.userGoal}</span>
              </div>
            )}
          </Panel>
        )}

        {/* A vs B readiness */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground">Config A · control</div>
            <div className="font-display font-semibold text-sm font-mono">{configAName}</div>
            {job.runIdA ? (
              <div className="flex items-center gap-2 flex-wrap">
                <ReadinessBadge runId={job.runIdA} />
                <Link
                  to="/runs/$runId"
                  params={{ runId: job.runIdA }}
                  className="text-xs text-primary hover:underline"
                >
                  {job.runIdA}
                </Link>
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                {isRunning && job.phase === "running-A" ? "Running…" : "Pending"}
              </div>
            )}
          </Panel>

          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground">Config B · variant</div>
            <div className="font-display font-semibold text-sm font-mono">{configBName}</div>
            {job.runIdB ? (
              <div className="flex items-center gap-2 flex-wrap">
                <ReadinessBadge runId={job.runIdB} />
                <Link
                  to="/runs/$runId"
                  params={{ runId: job.runIdB }}
                  className="text-xs text-primary hover:underline"
                >
                  {job.runIdB}
                </Link>
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                {isRunning && job.phase === "running-B" ? "Running…" : "Pending"}
              </div>
            )}
          </Panel>
        </div>

        {/* L3-PRED-04 — Per-persona comparison */}
        {report?.personaComparison && report.personaComparison.length > 0 && (
          <Panel className="overflow-hidden">
            <div className="p-4 border-b border-border flex items-center gap-2">
              <span className="font-display font-semibold text-sm">Per-persona results</span>
              <Chip tone="violet">L3-PRED-04</Chip>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2/40">
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium">
                    Persona
                  </th>
                  <th className="text-center px-4 py-2 text-xs text-muted-foreground font-medium">
                    A (control)
                  </th>
                  <th className="text-center px-4 py-2 text-xs text-muted-foreground font-medium">
                    B (variant)
                  </th>
                  <th className="text-center px-4 py-2 text-xs text-muted-foreground font-medium">
                    Δ
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {report.personaComparison.map((row) => {
                  const improved =
                    row.gradeA === "fail" && row.gradeB !== "fail"
                      ? true
                      : row.gradeA === "partial" && row.gradeB === "pass"
                        ? true
                        : false;
                  const regressed =
                    row.gradeB === "fail" && row.gradeA !== "fail"
                      ? true
                      : row.gradeB === "partial" && row.gradeA === "pass"
                        ? true
                        : false;
                  return (
                    <tr key={row.id} className="hover:bg-surface-2/30">
                      <td className="px-4 py-2.5 font-medium">{row.name}</td>
                      <td
                        className={`px-4 py-2.5 text-center font-mono ${GRADE_COLORS[row.gradeA] ?? ""}`}
                      >
                        {row.gradeA}
                      </td>
                      <td
                        className={`px-4 py-2.5 text-center font-mono ${GRADE_COLORS[row.gradeB] ?? ""}`}
                      >
                        {row.gradeB}
                      </td>
                      <td className="px-4 py-2.5 text-center text-xs">
                        {improved ? (
                          <span className="text-ready">↑ improved</span>
                        ) : regressed ? (
                          <span className="text-danger">↓ regressed</span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        )}

        {/* New + resolved issues */}
        {job.status === "done" && (newIssues.length > 0 || resolvedIssues.length > 0) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {newIssues.length > 0 && (
              <Panel className="p-5 space-y-3">
                <div className="text-xs font-medium text-danger">
                  New issues in variant B ({newIssues.length})
                </div>
                <ul className="space-y-1">
                  {(newIssues as Array<Record<string, string>>).slice(0, 5).map((issue, i) => (
                    <li key={i} className="text-xs text-muted-foreground flex gap-2">
                      <span className="font-mono text-danger shrink-0">{issue.severity}</span>
                      <span>{issue.title}</span>
                    </li>
                  ))}
                </ul>
              </Panel>
            )}
            {resolvedIssues.length > 0 && (
              <Panel className="p-5 space-y-3">
                <div className="text-xs font-medium text-ready">
                  Resolved in variant B ({resolvedIssues.length})
                </div>
                <ul className="space-y-1">
                  {(resolvedIssues as Array<Record<string, string>>).slice(0, 5).map((issue, i) => (
                    <li key={i} className="text-xs text-muted-foreground flex gap-2">
                      <span className="font-mono text-ready shrink-0">{issue.severity}</span>
                      <span>{issue.title}</span>
                    </li>
                  ))}
                </ul>
              </Panel>
            )}
          </div>
        )}

        {/* Narrative */}
        {narrative && (
          <Panel className="p-5 space-y-3">
            <div className="flex items-center gap-2">
              <GitCompare className="size-4 text-primary" />
              <span className="font-display font-semibold text-sm">What changed</span>
              {(narrative as Record<string, string>).source && (
                <Chip tone="info">{(narrative as Record<string, string>).source}</Chip>
              )}
            </div>
            {(narrative as Record<string, string>).executiveSummary && (
              <p className="text-sm">{(narrative as Record<string, string>).executiveSummary}</p>
            )}
            {(narrative as Record<string, string>).founderSummary && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-muted-foreground">Founder view</div>
                <p className="text-sm text-muted-foreground">
                  {(narrative as Record<string, string>).founderSummary}
                </p>
              </div>
            )}
          </Panel>
        )}

        {/* Full compare link */}
        {job.runIdA && job.runIdB && (
          <div className="flex">
            <Link
              to="/compare"
              search={{ a: job.runIdA, b: job.runIdB }}
              className="flex items-center gap-2 text-sm px-4 py-2 rounded-md border border-primary/40 text-primary hover:bg-primary/5"
            >
              <GitCompare className="size-4" />
              Open full compare — A vs B
            </Link>
          </div>
        )}

        {/* L3-PRED-05 — Experiment chat */}
        {job.status === "done" && <ExperimentChatPanel jobId={jobId} live={live} />}

        {isRunning && (
          <Panel className="p-4 text-sm text-muted-foreground flex items-center gap-2">
            <Loader2 className="size-4 animate-spin" />
            {PHASE_LABELS[job.phase] ?? "Running…"} Polling every 2 seconds.
          </Panel>
        )}
      </div>
    </div>
  );
}
