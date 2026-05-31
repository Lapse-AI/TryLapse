import { Fragment, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, Chip, SeverityChip } from "@/components/ui-bits";
import type { Annotation, Issue, RunBundle, StepSnapshot } from "@/lib/mock-data";
import { formatDurationMs } from "@/lib/mock-data";
import { artifactUrl } from "@/lib/api/client";
import { useAddAnnotation, useRunDiff } from "@/lib/api/hooks";
import {
  copyReproToClipboard,
  downloadArtifact,
  downloadRunBundleArtifacts,
  EXPORT_ITEMS,
  runArtifactRelPath,
} from "@/lib/run-export";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Camera } from "lucide-react";

export function EvidenceDialog({
  issue,
  runId,
  children,
}: {
  issue: Issue;
  runId: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [copying, setCopying] = useState(false);

  const handleCopyRepro = async () => {
    setCopying(true);
    try {
      await copyReproToClipboard(issue, runId);
      toast.success("Repro copied to clipboard");
    } catch {
      toast.error("Could not copy repro");
    } finally {
      setCopying(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild onClick={() => setOpen(true)}>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <SeverityChip s={issue.severity} />
            <Chip>{issue.dimension}</Chip>
            <Chip tone={issue.confidence === "high" ? "info" : "warn"}>{issue.confidence}</Chip>
          </div>
          <DialogTitle className="font-display">{issue.title}</DialogTitle>
          <DialogDescription>
            {issue.persona} · {issue.journey} · <span className="font-mono">{issue.stepId}</span>
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="aspect-video rounded-md border border-border bg-surface-2 overflow-hidden">
            {issue.screenshotPath ? (
              <img
                src={artifactUrl(issue.screenshotPath)}
                alt={`Screenshot for ${issue.stepId}`}
                className="w-full h-full object-contain bg-black/5"
              />
            ) : (
              <div className="h-full grid-bg flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Camera className="size-6 mx-auto mb-2 opacity-60" />
                  <div className="text-xs font-mono">screenshot · {issue.stepId} · 1280×720</div>
                </div>
              </div>
            )}
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Evidence</div>
            <p className="text-sm font-mono bg-surface-2 border border-border rounded-md p-3">
              {issue.evidence}
            </p>
          </div>
          {issue.severityReason && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Why {issue.severity}</div>
              <p className="text-sm">{issue.severityReason}</p>
            </div>
          )}
          {issue.suggestion && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Suggestion (no auto-fix)</div>
              <p className="text-sm text-foreground/90">{issue.suggestion}</p>
            </div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Owner</div>
              <div className="font-medium mt-0.5 capitalize">{issue.owner}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Recurrence</div>
              <div className="font-medium mt-0.5">×{issue.recurring} runs</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Step</div>
              <div className="font-mono mt-0.5 text-xs">{issue.stepId}</div>
            </div>
            {issue.personaImpact && (
              <div className="col-span-2">
                <div className="text-xs text-muted-foreground">Persona impact</div>
                <div className="text-xs mt-0.5">{issue.personaImpact}</div>
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <button
            type="button"
            disabled={copying}
            onClick={() => void handleCopyRepro()}
            className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 disabled:opacity-50"
          >
            {copying ? "Copying…" : "Copy repro"}
          </button>
          <Link
            to="/runs/$runId"
            params={{ runId }}
            search={{ tab: "steps", step: issue.stepId }}
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 inline-flex items-center"
          >
            Open in step timeline
          </Link>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function StepsTable({
  steps,
  highlightStepId,
}: {
  steps: StepSnapshot[];
  highlightStepId?: string;
}) {
  if (!steps.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        No steps recorded for this run.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-xs text-muted-foreground">
          <tr className="border-b border-border bg-surface-2/40">
            <th className="text-left px-5 py-2 font-medium">Step ID</th>
            <th className="text-left px-5 py-2 font-medium">Journey</th>
            <th className="text-left px-5 py-2 font-medium">Action</th>
            <th className="text-left px-5 py-2 font-medium">Outcome</th>
            <th className="text-left px-5 py-2 font-medium">Duration</th>
            <th className="text-left px-5 py-2 font-medium">URL</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((s) => (
            <Fragment key={s.stepId}>
            <tr
              id={`step-${s.stepId}`}
              className={`border-b border-border hover:bg-surface-2/30 ${
                highlightStepId === s.stepId ? "bg-primary/10 ring-1 ring-primary/30" : ""
              }`}
            >
              <td className="px-5 py-3 font-mono text-xs">
                {s.stepId}
                {s.flaky && (
                  <span className="ml-2">
                    <Chip tone="warn">flaky</Chip>
                  </span>
                )}
              </td>
              <td className="px-5 py-3 text-xs">{s.journeyId}</td>
              <td className="px-5 py-3">
                <div>{s.action}</div>
                {s.action === "explore" && s.exploreSummary && (
                  <p className="text-xs text-muted-foreground mt-1 max-w-md whitespace-pre-wrap">
                    {s.exploreSummary}
                  </p>
                )}
              </td>
              <td className="px-5 py-3">
                <Chip
                  tone={
                    s.outcome === "pass"
                      ? "ready"
                      : s.outcome === "partial"
                        ? "warn"
                        : s.outcome === "fail"
                          ? "danger"
                          : "neutral"
                  }
                >
                  {s.outcome}
                </Chip>
              </td>
              <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                {formatDurationMs(s.durationMs)}
              </td>
              <td className="px-5 py-3 font-mono text-xs max-w-[200px] truncate text-muted-foreground">
                {(s.finalUrl ?? s.requestedUrl ?? "—").slice(0, 60)}
              </td>
            </tr>
            {s.action === "explore" && (s.exploreLog?.length || s.exploreSummary) ? (
              <tr key={`${s.stepId}-explore`} className="border-b border-border last:border-0">
                <td colSpan={6} className="px-5 py-3 bg-surface-2/40 text-xs space-y-2">
                  {s.exploreSummary && (
                    <p className="text-sm leading-relaxed">{s.exploreSummary}</p>
                  )}
                  {s.exploreLog?.map((rnd) => (
                    <div key={rnd.round} className="font-mono text-[11px] text-muted-foreground">
                      Round {rnd.round}
                      {rnd.rationale ? ` — ${rnd.rationale}` : ""}
                      {(rnd.actions ?? []).map((a, i) => (
                        <span key={i} className="ml-2">
                          [{a.outcome}] {a.action}
                          {a.intent ? `: ${a.intent}` : ""}
                        </span>
                      ))}
                    </div>
                  ))}
                </td>
              </tr>
            ) : null}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { RunNarrativePanel } from "./run-detail/RunNarrativePanel";

export function ScorecardPanel({ markdown }: { markdown: string }) {
  return (
    <pre className="p-5 text-[12.5px] font-mono leading-relaxed overflow-x-auto bg-surface-2/30 text-foreground/95 whitespace-pre-wrap">
      {markdown}
    </pre>
  );
}

export function SitemapPanel({ markdown }: { markdown: string }) {
  return (
    <pre className="p-5 text-[12.5px] font-mono leading-relaxed overflow-x-auto bg-surface-2/30 text-foreground/95 whitespace-pre-wrap">
      {markdown}
    </pre>
  );
}

export function ScreenshotGallery({
  shots,
}: {
  shots: { path: string; stepId: string; label: string }[];
}) {
  if (!shots.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">No screenshots captured.</div>
    );
  }
  return (
    <div className="p-5 grid grid-cols-2 md:grid-cols-3 gap-4">
      {shots.map((s) => (
        <figure
          key={s.stepId}
          className="border border-border rounded-lg overflow-hidden bg-surface-2/30"
        >
          <div className="aspect-video bg-black/5">
            <img
              src={artifactUrl(s.path)}
              alt={s.stepId}
              className="w-full h-full object-contain"
              loading="lazy"
            />
          </div>
          <figcaption className="p-2 text-[11px] text-muted-foreground border-t border-border">
            <div className="font-medium text-foreground truncate">{s.label}</div>
            <div className="font-mono truncate">{s.stepId}</div>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export function DiffPanel({ runA, runB }: { runA: string; runB: string }) {
  const { data: diff, isLoading, error } = useRunDiff(runA, runB);
  if (isLoading) {
    return <div className="p-8 text-center text-sm text-muted-foreground">Loading diff…</div>;
  }
  if (error || !diff) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        Could not diff runs — one or both not found.
      </div>
    );
  }
  const cn = diff.narrative;

  return (
    <div className="p-5 space-y-4">
      {cn && (
        <Panel className="p-4 md:p-5 space-y-3 border-primary/20 bg-primary/5">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="font-display font-semibold">What changed</div>
            <Chip tone={cn.verdict === "improved" ? "ready" : cn.verdict === "regressed" ? "danger" : "warn"}>
              {cn.verdict}
            </Chip>
            <Chip tone="neutral">{cn.source === "llm+template" ? "AI + rules" : "Rules"}</Chip>
          </div>
          <p className="text-sm leading-relaxed">{cn.headline}</p>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-muted-foreground mb-1">For founders</div>
              <p className="whitespace-pre-wrap">{cn.forFounders}</p>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">For engineering</div>
              <p className="whitespace-pre-wrap">{cn.forEngineering}</p>
            </div>
          </div>
        </Panel>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Readiness</div>
          <div className="font-mono text-sm mt-1">
            {diff.readinessA} → {diff.readinessB}
          </div>
        </Panel>
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Issues</div>
          <div className="font-mono text-sm mt-1">
            {diff.issuesA} → {diff.issuesB}
          </div>
        </Panel>
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Pages crawled</div>
          <div className="font-mono text-sm mt-1">
            {diff.pagesA} → {diff.pagesB}
          </div>
        </Panel>
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Changed steps</div>
          <div className="font-mono text-sm mt-1">{diff.changedSteps.length}</div>
        </Panel>
      </div>
      {diff.newIssues.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">New issues in {runB}</div>
          <ul className="text-sm space-y-1">
            {diff.newIssues.map((i) => (
              <li key={i} className="text-danger">
                + {i}
              </li>
            ))}
          </ul>
        </div>
      )}
      {diff.resolvedIssues.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">Resolved since {runA}</div>
          <ul className="text-sm space-y-1">
            {diff.resolvedIssues.map((i) => (
              <li key={i} className="text-ready">
                − {i}
              </li>
            ))}
          </ul>
        </div>
      )}
      <details className="group">
        <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
          Advanced · raw diff JSON
        </summary>
        <pre className="mt-2 text-[11px] font-mono bg-surface-2 border border-border rounded-lg p-4 overflow-x-auto">
          {JSON.stringify(diff, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export function AnnotationsPanel({
  runId: _runId,
  annotations,
}: {
  runId: string;
  annotations: Annotation[];
}) {
  if (!annotations.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        No human annotations yet. Agree, disagree, or pin findings from the Issues tab.
      </div>
    );
  }
  return (
    <div className="divide-y divide-border">
      {annotations.map((a) => (
        <div key={a.id} className="p-4 flex items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs text-muted-foreground">{a.author}</span>
            <Chip
              tone={
                a.action === "agreed"
                  ? "ready"
                  : a.action === "false positive"
                    ? "warn"
                    : a.action === "pinned"
                      ? "violet"
                      : "info"
              }
            >
              {a.action}
            </Chip>
            <span>
              {a.targetType} · <span className="font-mono">{a.targetId}</span>
            </span>
            {a.note && <span className="text-muted-foreground text-xs">— {a.note}</span>}
          </div>
          <span className="text-[11px] text-muted-foreground font-mono shrink-0">
            {a.at.slice(0, 10)}
          </span>
        </div>
      ))}
    </div>
  );
}

type AnnotationAction = Extract<Annotation["action"], "agreed" | "disagree" | "false positive">;

const ANNOTATION_ACTIONS: {
  action: AnnotationAction;
  label: string;
  tone: "ready" | "info" | "warn";
}[] = [
  { action: "agreed", label: "Agree", tone: "ready" },
  { action: "disagree", label: "Disagree", tone: "info" },
  { action: "false positive", label: "False positive", tone: "warn" },
];

export function IssueAnnotationActions({
  runId,
  issue,
  existing,
}: {
  runId: string;
  issue: Issue;
  existing?: Annotation;
}) {
  const addAnnotation = useAddAnnotation(runId);

  const submit = (action: AnnotationAction) => {
    const ann: Annotation = {
      id: `ann_${Date.now()}`,
      runId,
      targetType: "issue",
      targetId: issue.id,
      action,
      author: "operator",
      at: new Date().toISOString(),
    };
    addAnnotation.mutate(ann, {
      onSuccess: () => toast.success(`Marked ${action}`),
      onError: () => toast.error("Could not save annotation"),
    });
  };

  if (existing) {
    return (
      <Chip
        tone={
          existing.action === "agreed"
            ? "ready"
            : existing.action === "false positive"
              ? "warn"
              : "info"
        }
      >
        {existing.action}
      </Chip>
    );
  }

  return (
    <div className="flex items-center gap-1 shrink-0">
      {ANNOTATION_ACTIONS.map(({ action, label, tone }) => (
        <button
          key={action}
          type="button"
          disabled={addAnnotation.isPending}
          onClick={() => submit(action)}
          className="text-[10px] font-mono px-2 py-1 rounded-md border border-border hover:bg-surface-2 disabled:opacity-50"
          style={{ color: `var(--${tone})` }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function ExportMenu({ runId, bundle }: { runId: string; bundle: RunBundle }) {
  const [busy, setBusy] = useState<string | null>(null);

  const downloadOne = async (kind: (typeof EXPORT_ITEMS)[number]["kind"], label: string) => {
    setBusy(label);
    try {
      await downloadArtifact(runArtifactRelPath(runId, kind), `${runId}-${label}`);
      toast.success(`Downloaded ${label}`);
    } catch {
      toast.error(`Could not download ${label} — is ./rehearse serve running?`);
    } finally {
      setBusy(null);
    }
  };

  const downloadAll = async () => {
    setBusy("all");
    try {
      const { ok, failed } = await downloadRunBundleArtifacts(bundle);
      if (failed.length) {
        toast.warning(`Downloaded ${ok} files; missing: ${failed.slice(0, 5).join(", ")}`);
      } else {
        toast.success(`Downloaded ${ok} artifacts`);
      }
    } catch {
      toast.error("Bulk download failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2"
        >
          Export
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export run artifacts</DialogTitle>
          <DialogDescription>
            Files from launch-rehearsal/artifacts/ — served at /files/ when rehearse serve is
            running.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {EXPORT_ITEMS.map(({ kind, label }) => (
            <button
              key={label}
              type="button"
              disabled={busy !== null}
              onClick={() => void downloadOne(kind, label)}
              className="w-full text-left px-3 py-2 rounded-md border border-border hover:bg-surface-2 font-mono text-sm disabled:opacity-50"
            >
              {busy === label ? `Downloading ${label}…` : label}
            </button>
          ))}
          {bundle.screenshots.length > 0 && (
            <p className="text-[11px] text-muted-foreground px-1 pt-1">
              Download all includes {bundle.screenshots.length} PNG screenshots (no zip yet).
            </p>
          )}
        </div>
        <DialogFooter>
          <button
            type="button"
            disabled={busy !== null}
            onClick={() => void downloadAll()}
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
          >
            {busy === "all" ? "Downloading…" : "Download all"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
