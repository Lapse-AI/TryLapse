import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, ShieldAlert, Users, Sparkles, AlertTriangle } from "lucide-react";
import { PageHeader, Panel, SectionTitle, Chip, ClientTime, Stat } from "@/components/ui-bits";
import { CrawlTreeGraph } from "@/components/crawl-tree-graph";
import { useAdminWorkspaceDetail } from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";

export const Route = createFileRoute("/admin/$slug")({
  head: ({ params }) => ({ meta: [{ title: `${params.slug} — Admin — Launch Rehearsal` }] }),
  component: WorkspaceDetailPage,
});

function isForbidden(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403;
}

function asString(v: unknown): string | undefined {
  return typeof v === "string" ? v : undefined;
}

function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function WorkspaceDetailPage() {
  const { slug } = Route.useParams();
  const { data: ws, error, isLoading } = useAdminWorkspaceDetail(slug);

  if (isForbidden(error)) {
    return (
      <div className="p-8">
        <Panel className="p-6 flex items-center gap-3 border-danger/30 bg-danger/5">
          <ShieldAlert className="size-5 text-danger shrink-0" />
          <div className="text-sm">Admin access required.</div>
        </Panel>
      </div>
    );
  }
  if (error) {
    return (
      <div className="p-8">
        <Panel className="p-6 text-sm text-muted-foreground">Workspace not found.</Panel>
      </div>
    );
  }
  if (isLoading || !ws) {
    return (
      <div className="p-8">
        <Panel className="p-6 text-sm text-muted-foreground">Loading…</Panel>
      </div>
    );
  }

  const model = ws.productModel as Record<string, unknown> | null;
  const coreFeatures = model ? asArray(model.core_features) : [];
  const workflows = model ? asArray(model.primary_workflows) : [];
  const userTypes = model ? asArray(model.user_types_observed) : [];
  const qualityConcerns = model ? asArray(model.quality_concerns) : [];

  return (
    <div>
      <PageHeader
        eyebrow="internal"
        title={ws.name}
        description={
          <span className="flex items-center gap-2 flex-wrap">
            <Link to="/admin" className="inline-flex items-center gap-1 hover:underline">
              <ArrowLeft className="size-3.5" /> Company
            </Link>
            <span className="text-muted-foreground">·</span>
            <span className="font-mono text-xs">{ws.slug}</span>
            <span className="text-muted-foreground">·</span>
            <span className="font-mono text-xs truncate">{ws.targetUrl}</span>
          </span>
        }
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <Stat label="Plan" value={ws.plan} />
            <Stat label="Total runs" value={String(ws.totalRuns)} />
            <Stat
              label="Runs this month"
              value={
                ws.runLimit != null
                  ? `${ws.runsThisMonth} / ${ws.runLimit}`
                  : String(ws.runsThisMonth)
              }
            />
            <Stat label="Members" value={String(ws.memberCount)} />
            <Stat
              label="Status"
              value={ws.neverRan ? "Never ran" : (ws.lastRunStatus ?? "—")}
              tone={ws.neverRan ? "danger" : ws.lastRunStatus === "failed" ? "danger" : undefined}
            />
          </div>
          <div className="mt-4 text-xs text-muted-foreground">
            Owner: {ws.ownerName} ({ws.ownerEmail}) · Created <ClientTime iso={ws.createdAt} />
          </div>
          {ws.lastRunError && (
            <div className="mt-3 text-xs text-danger font-mono">{ws.lastRunError}</div>
          )}
        </Panel>

        {ws.configError && (
          <Panel className="p-4 flex items-center gap-3 border-danger/30 bg-danger/5">
            <AlertTriangle className="size-4 text-danger shrink-0" />
            <div className="text-sm font-mono">{ws.configError}</div>
          </Panel>
        )}

        <Panel className="p-6">
          <SectionTitle eyebrow="crawl" title="Crawl coverage" />
          <CrawlTreeGraph configId={ws.slug} />
        </Panel>

        {model && (
          <Panel className="p-6">
            <SectionTitle
              eyebrow="product intelligence"
              title="What the AI found"
              action={<Chip tone="neutral">{asString(model.source) ?? "unknown"}</Chip>}
            />
            {asString(model.purpose) && (
              <p className="text-sm text-muted-foreground mb-4">{asString(model.purpose)}</p>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {coreFeatures.length > 0 && (
                <div>
                  <div className="text-xs text-muted-foreground mb-2">Core features</div>
                  <ul className="text-sm space-y-1 list-disc list-inside">
                    {coreFeatures.map((f, i) => (
                      <li key={i}>{String(f)}</li>
                    ))}
                  </ul>
                </div>
              )}
              {userTypes.length > 0 && (
                <div>
                  <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                    <Users className="size-3" /> User types observed
                  </div>
                  <ul className="text-sm space-y-1 list-disc list-inside">
                    {userTypes.map((u, i) => (
                      <li key={i}>{typeof u === "string" ? u : JSON.stringify(u)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            {workflows.length > 0 && (
              <div className="mt-5">
                <div className="text-xs text-muted-foreground mb-2">Primary workflows</div>
                <ul className="text-sm space-y-1.5">
                  {workflows.map((w, i) => {
                    const wf = w as Record<string, unknown>;
                    return (
                      <li key={i} className="flex items-center gap-2">
                        <span>
                          {asString(wf.name) ?? asString(wf.entry_point) ?? `Workflow ${i + 1}`}
                        </span>
                        {wf.frequency != null && <Chip tone="neutral">{String(wf.frequency)}</Chip>}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
            {qualityConcerns.length > 0 && (
              <div className="mt-5">
                <div className="text-xs text-muted-foreground mb-2">Quality concerns</div>
                <ul className="text-sm space-y-1.5">
                  {qualityConcerns.map((q, i) => {
                    const qc = q as Record<string, unknown>;
                    const severity = asString(qc.severity);
                    return (
                      <li key={i} className="flex items-start gap-2">
                        <Chip
                          tone={
                            severity === "critical" || severity === "moderate" ? "warn" : "neutral"
                          }
                        >
                          {severity ?? "minor"}
                        </Chip>
                        <span>{asString(qc.description) ?? JSON.stringify(qc)}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </Panel>
        )}

        <Panel className="overflow-hidden">
          <SectionTitle
            eyebrow="config"
            title={`Personas (${ws.personas.length})`}
            action={<Sparkles className="size-3.5 text-muted-foreground" />}
          />
          {ws.personas.length === 0 ? (
            <div className="px-4 pb-4 text-sm text-muted-foreground">
              No personas configured yet.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border bg-surface-2/40">
                  <th className="text-left px-4 py-2.5 font-medium">Name</th>
                  <th className="text-left px-4 py-2.5 font-medium">Role</th>
                  <th className="text-left px-4 py-2.5 font-medium">Tech literacy</th>
                  <th className="text-left px-4 py-2.5 font-medium">Patience</th>
                  <th className="text-left px-4 py-2.5 font-medium">Trust</th>
                  <th className="text-left px-4 py-2.5 font-medium">Goals</th>
                </tr>
              </thead>
              <tbody>
                {ws.personas.map((p) => (
                  <tr
                    key={p.id}
                    className="border-b border-border last:border-0 hover:bg-surface-2/40"
                  >
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{p.role}</td>
                    <td className="px-4 py-3">
                      <Chip tone="neutral">{p.techLiteracy}</Chip>
                    </td>
                    <td className="px-4 py-3">
                      <Chip tone="neutral">{p.patience}</Chip>
                    </td>
                    <td className="px-4 py-3">
                      <Chip tone="neutral">{p.trustLevel}</Chip>
                    </td>
                    <td
                      className="px-4 py-3 text-xs text-muted-foreground max-w-[300px] truncate"
                      title={p.goals.join(", ")}
                    >
                      {p.goals.join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        {ws.journeys.length > 0 && (
          <Panel className="overflow-hidden">
            <SectionTitle eyebrow="config" title={`Journeys (${ws.journeys.length})`} />
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border bg-surface-2/40">
                  <th className="text-left px-4 py-2.5 font-medium">Name</th>
                  <th className="text-left px-4 py-2.5 font-medium">Steps</th>
                  <th className="text-left px-4 py-2.5 font-medium">Personas</th>
                </tr>
              </thead>
              <tbody>
                {ws.journeys.map((j) => (
                  <tr
                    key={j.id}
                    className="border-b border-border last:border-0 hover:bg-surface-2/40"
                  >
                    <td className="px-4 py-3 font-medium">{j.name}</td>
                    <td className="px-4 py-3 font-mono tabular-nums">{j.stepCount}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {j.personaIds.length > 0 ? j.personaIds.join(", ") : "all personas"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        )}

        <Panel className="overflow-hidden">
          <SectionTitle eyebrow="runs" title={`Run history (${ws.jobs.length})`} />
          {ws.jobs.length === 0 ? (
            <div className="px-4 pb-4 text-sm text-muted-foreground">
              No rehearsal jobs have run yet for this workspace.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border bg-surface-2/40">
                  <th className="text-left px-4 py-2.5 font-medium">Job</th>
                  <th className="text-left px-4 py-2.5 font-medium">Status</th>
                  <th className="text-left px-4 py-2.5 font-medium">Started</th>
                  <th className="text-left px-4 py-2.5 font-medium">Error</th>
                </tr>
              </thead>
              <tbody>
                {ws.jobs.map((j) => (
                  <tr
                    key={j.id}
                    className="border-b border-border last:border-0 hover:bg-surface-2/40"
                  >
                    <td className="px-4 py-3 font-mono text-xs">{j.id}</td>
                    <td className="px-4 py-3">
                      <Chip
                        tone={
                          j.status === "failed"
                            ? "danger"
                            : j.status === "done"
                              ? "ready"
                              : "neutral"
                        }
                      >
                        {j.status}
                      </Chip>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {j.startedAt && <ClientTime iso={j.startedAt} />}
                    </td>
                    <td
                      className="px-4 py-3 text-xs text-danger max-w-[300px] truncate"
                      title={j.error ?? undefined}
                    >
                      {j.error ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel className="overflow-hidden">
          <SectionTitle eyebrow="access" title={`Members (${ws.members.length})`} />
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr className="border-b border-border bg-surface-2/40">
                <th className="text-left px-4 py-2.5 font-medium">Name</th>
                <th className="text-left px-4 py-2.5 font-medium">Email</th>
                <th className="text-left px-4 py-2.5 font-medium">Role</th>
                <th className="text-left px-4 py-2.5 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody>
              {ws.members.map((m) => (
                <tr
                  key={m.userId}
                  className="border-b border-border last:border-0 hover:bg-surface-2/40"
                >
                  <td className="px-4 py-3">{m.name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{m.email}</td>
                  <td className="px-4 py-3">
                    <Chip tone="neutral">{m.role}</Chip>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    <ClientTime iso={m.joinedAt} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}
