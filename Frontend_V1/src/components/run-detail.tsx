import { Panel, Chip, SeverityChip } from "@/components/ui-bits";
import type { Annotation, Issue, StepSnapshot } from "@/lib/mock-data";
import { formatDurationMs } from "@/lib/mock-data";
import { artifactUrl } from "@/lib/api/client";
import { useRunDiff } from "@/lib/api/hooks";
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

export function EvidenceDialog({ issue, children }: { issue: Issue; children: React.ReactNode }) {
  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>
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
            className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2"
          >
            Copy repro
          </button>
          <button
            type="button"
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90"
          >
            Open in step timeline
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function StepsTable({ steps }: { steps: StepSnapshot[] }) {
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
            <tr
              key={s.stepId}
              className="border-b border-border last:border-0 hover:bg-surface-2/30"
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
              <td className="px-5 py-3">{s.action}</td>
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
          ))}
        </tbody>
      </table>
    </div>
  );
}

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
  return (
    <div className="p-5 space-y-4">
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
      <pre className="text-[11px] font-mono bg-surface-2 border border-border rounded-lg p-4 overflow-x-auto">
        {JSON.stringify(diff, null, 2)}
      </pre>
    </div>
  );
}

export function AnnotationsPanel({ annotations }: { annotations: Annotation[] }) {
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

export function ExportMenu() {
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
          <DialogDescription>Same files the CLI writes under artifacts/</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {[
            "scorecard.md",
            "run.json",
            "sitemap.json",
            "sitemap.md",
            "analysis.json",
            "screenshots.zip",
          ].map((f) => (
            <button
              key={f}
              type="button"
              className="w-full text-left px-3 py-2 rounded-md border border-border hover:bg-surface-2 font-mono text-sm"
            >
              {f}
            </button>
          ))}
        </div>
        <DialogFooter>
          <button
            type="button"
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground"
          >
            Download all
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
