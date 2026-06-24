import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, ShieldAlert } from "lucide-react";
import { PageHeader, Panel, SectionTitle, Chip, ClientTime, Stat } from "@/components/ui-bits";
import {
  useAdminSummary,
  useAdminWorkspaces,
  useAdminUsers,
  useAdminActivity,
} from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";

export const Route = createFileRoute("/admin")({
  head: () => ({ meta: [{ title: "Admin — Launch Rehearsal" }] }),
  component: AdminPage,
});

function isForbidden(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403;
}

function SummarySection() {
  const { data, error, isLoading } = useAdminSummary();

  if (isForbidden(error)) {
    return (
      <Panel className="p-6 flex items-center gap-3 border-danger/30 bg-danger/5">
        <ShieldAlert className="size-5 text-danger shrink-0" />
        <div className="text-sm">
          Admin access required. Set{" "}
          <code className="font-mono text-xs">REHEARSE_ADMIN_EMAILS</code> to include your account,
          or leave it unset to allow any signed-in user.
        </div>
      </Panel>
    );
  }
  if (isLoading || !data) {
    return <Panel className="p-6 text-sm text-muted-foreground">Loading…</Panel>;
  }

  return (
    <Panel className="p-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <Stat label="Users" value={String(data.totalUsers)} />
        <Stat label="Workspaces" value={String(data.totalWorkspaces)} />
        <Stat
          label="Never run"
          value={String(data.workspacesNeverRun)}
          tone={data.workspacesNeverRun > 0 ? "danger" : undefined}
        />
        <Stat
          label="Recent failures"
          value={String(data.failedJobsRecent)}
          tone={data.failedJobsRecent > 0 ? "warn" : undefined}
        />
      </div>
      {data.neverRunSlugs.length > 0 && (
        <div className="mt-5 flex items-start gap-2.5 px-3 py-2.5 rounded-md border border-danger/30 bg-danger/5">
          <AlertTriangle className="size-4 text-danger shrink-0 mt-0.5" />
          <div className="text-sm">
            <span className="font-medium">
              {data.neverRunSlugs.length} workspace{data.neverRunSlugs.length !== 1 ? "s" : ""}{" "}
              created but never ran a job:
            </span>{" "}
            <span className="font-mono text-xs">{data.neverRunSlugs.join(", ")}</span>
          </div>
        </div>
      )}
    </Panel>
  );
}

function WorkspacesSection() {
  const { data: workspaces, error, isLoading } = useAdminWorkspaces();
  if (isForbidden(error) || isLoading || !workspaces) return null;

  return (
    <Panel className="overflow-hidden">
      <SectionTitle eyebrow="company" title="Workspaces" />
      <table className="w-full text-sm">
        <thead className="text-xs text-muted-foreground">
          <tr className="border-b border-border bg-surface-2/40">
            <th className="text-left px-4 py-2.5 font-medium">Workspace</th>
            <th className="text-left px-4 py-2.5 font-medium">Owner</th>
            <th className="text-left px-4 py-2.5 font-medium">Target URL</th>
            <th className="text-left px-4 py-2.5 font-medium">Plan</th>
            <th className="text-left px-4 py-2.5 font-medium">Runs</th>
            <th className="text-left px-4 py-2.5 font-medium">Last run</th>
            <th className="text-left px-4 py-2.5 font-medium">Members</th>
          </tr>
        </thead>
        <tbody>
          {workspaces.map((ws) => (
            <tr
              key={ws.id}
              className={`border-b border-border last:border-0 ${ws.neverRan ? "bg-danger/5" : "hover:bg-surface-2/40"}`}
            >
              <td className="px-4 py-3">
                <div className="font-medium">{ws.name}</div>
                <div className="text-xs font-mono text-muted-foreground">{ws.slug}</div>
              </td>
              <td className="px-4 py-3 text-xs">
                <div>{ws.ownerName}</div>
                <div className="text-muted-foreground">{ws.ownerEmail}</div>
              </td>
              <td
                className="px-4 py-3 font-mono text-xs max-w-[260px] truncate"
                title={ws.targetUrl}
              >
                {ws.targetUrl}
              </td>
              <td className="px-4 py-3">
                <Chip tone="neutral">{ws.plan}</Chip>
              </td>
              <td className="px-4 py-3 font-mono tabular-nums">
                {ws.totalRuns}
                {ws.runLimit != null && (
                  <span className="text-muted-foreground"> / {ws.runLimit}</span>
                )}
              </td>
              <td className="px-4 py-3">
                {ws.neverRan ? (
                  <div className="text-xs">
                    <Chip tone="danger">never ran</Chip>
                    {ws.productAnalysis ? (
                      <div className="text-muted-foreground mt-1">
                        Onboarding analysis found {ws.productAnalysis.pageCount} page
                        {ws.productAnalysis.pageCount !== 1 ? "s" : ""}
                        {ws.productAnalysis.loginAttempted &&
                          (ws.productAnalysis.loginSucceeded
                            ? " · login succeeded"
                            : " · login failed")}
                      </div>
                    ) : (
                      <div className="text-muted-foreground mt-1">No analysis either</div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs">
                    <Chip
                      tone={
                        ws.lastRunStatus === "failed"
                          ? "danger"
                          : ws.lastRunStatus === "done"
                            ? "ready"
                            : "neutral"
                      }
                    >
                      {ws.lastRunStatus}
                    </Chip>
                    {ws.lastRunAt && (
                      <div className="text-muted-foreground mt-1">
                        <ClientTime iso={ws.lastRunAt} />
                      </div>
                    )}
                    {ws.lastRunError && (
                      <div
                        className="text-danger mt-1 max-w-[200px] truncate"
                        title={ws.lastRunError}
                      >
                        {ws.lastRunError}
                      </div>
                    )}
                  </div>
                )}
              </td>
              <td className="px-4 py-3 font-mono tabular-nums text-muted-foreground">
                {ws.memberCount}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

function UsersSection() {
  const { data: users, error, isLoading } = useAdminUsers();
  if (isForbidden(error) || isLoading || !users) return null;

  return (
    <Panel className="overflow-hidden">
      <SectionTitle eyebrow="company" title="Users" />
      <table className="w-full text-sm">
        <thead className="text-xs text-muted-foreground">
          <tr className="border-b border-border bg-surface-2/40">
            <th className="text-left px-4 py-2.5 font-medium">Name</th>
            <th className="text-left px-4 py-2.5 font-medium">Email</th>
            <th className="text-left px-4 py-2.5 font-medium">Signed up</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-b border-border last:border-0 hover:bg-surface-2/40">
              <td className="px-4 py-3">{u.name}</td>
              <td className="px-4 py-3 font-mono text-xs">{u.email}</td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                <ClientTime iso={u.createdAt} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

function ActivitySection() {
  const { data: jobs, error, isLoading } = useAdminActivity(50);
  if (isForbidden(error) || isLoading || !jobs) return null;

  return (
    <Panel className="overflow-hidden">
      <SectionTitle eyebrow="company" title="Recent activity" />
      <table className="w-full text-sm">
        <thead className="text-xs text-muted-foreground">
          <tr className="border-b border-border bg-surface-2/40">
            <th className="text-left px-4 py-2.5 font-medium">Job</th>
            <th className="text-left px-4 py-2.5 font-medium">Status</th>
            <th className="text-left px-4 py-2.5 font-medium">Config</th>
            <th className="text-left px-4 py-2.5 font-medium">Started</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id} className="border-b border-border last:border-0 hover:bg-surface-2/40">
              <td className="px-4 py-3 font-mono text-xs">{j.id}</td>
              <td className="px-4 py-3">
                <Chip
                  tone={
                    j.status === "failed" ? "danger" : j.status === "done" ? "ready" : "neutral"
                  }
                >
                  {j.status}
                </Chip>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground max-w-[260px] truncate">
                {j.config}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {j.startedAt && <ClientTime iso={j.startedAt} />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

function AdminPage() {
  return (
    <div>
      <PageHeader
        eyebrow="internal"
        title="Company"
        description="Every user, workspace, and run in this deployment — not scoped to a single workspace."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <SummarySection />
        <WorkspacesSection />
        <ActivitySection />
        <UsersSection />
      </div>
    </div>
  );
}
