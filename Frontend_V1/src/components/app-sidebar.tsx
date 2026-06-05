import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Activity,
  Network,
  GitBranch,
  TrendingUp,
  Bot,
  Bell,
  Settings,
  Plug,
  Terminal,
  ShieldCheck,
  GitCompare,
  Lightbulb,
  PlayCircle,
  BookOpen,
  Wand2,
} from "lucide-react";
import { formatRel } from "@/lib/mock-data";
import { useLatestRun, useWorkspace, useScopedActiveJobs } from "@/lib/api/hooks";
import { useTestGroup, displayTargetForGroup } from "@/hooks/use-test-group";
import { Chip } from "@/components/ui-bits";

const nav = [
  {
    group: "Monitor",
    items: [
      { to: "/", label: "Command center", icon: LayoutDashboard },
      { to: "/runs", label: "Runs", icon: Activity },
      { to: "/compare", label: "Compare runs", icon: GitCompare },
      { to: "/trends", label: "Trends", icon: TrendingUp },
      { to: "/alerts", label: "Alerts", icon: Bell },
      { to: "/recommendations", label: "Recommendations", icon: Lightbulb },
    ],
  },
  {
    group: "Author & rehearse",
    items: [
      { to: "/init", label: "Init wizard", icon: Wand2 },
      { to: "/library", label: "Journey library", icon: BookOpen },
      { to: "/config", label: "Config (YAML)", icon: Settings },
      { to: "/runner", label: "Runner", icon: PlayCircle },
    ],
  },
  {
    group: "Map",
    items: [
      { to: "/sitemap", label: "Site map", icon: Network },
      { to: "/workflows", label: "Workflows", icon: GitBranch },
    ],
  },
  { group: "Agents", items: [{ to: "/agents", label: "Agent control", icon: Bot }] },
  {
    group: "Platform",
    items: [
      { to: "/integrations", label: "Integrations", icon: Plug },
      { to: "/cli", label: "CLI", icon: Terminal },
    ],
  },
];

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const latest = useLatestRun();
  const { data: activeJobs = [] } = useScopedActiveJobs();
  const liveJob = activeJobs[0];
  const { data: workspace } = useWorkspace();
  const { group, resolvedConfigId } = useTestGroup();
  const targetLabel = displayTargetForGroup(group);

  return (
    <aside
      className="w-60 shrink-0 border-r border-sidebar-border text-sidebar-foreground flex flex-col backdrop-blur-xl"
      style={{ background: "color-mix(in oklab, white 76%, transparent)" }}
    >
      <div className="px-4 h-14 flex items-center gap-2.5 border-b border-sidebar-border/70">
        <div className="size-7 rounded-lg bg-primary/15 border border-primary/25 flex items-center justify-center shadow-[0_1px_3px_color-mix(in_oklab,var(--primary)_20%,transparent)]">
          <ShieldCheck className="size-4 text-primary" />
        </div>
        <div className="leading-tight">
          <div className="font-display font-semibold text-[15px] tracking-tight">Rehearsal</div>
          <div className="text-[11px] text-muted-foreground">
            <span className="px-1 py-px rounded bg-surface-2 border border-border text-[11px] font-mono">
              Monitor
            </span>
          </div>
        </div>
      </div>

      <div className="px-3 py-3 border-b border-sidebar-border">
        <button
          type="button"
          aria-label={workspace?.name ?? "Workspace"}
          className="w-full flex items-center justify-between px-2.5 py-2 rounded-md bg-sidebar-accent hover:bg-sidebar-accent/70 border border-sidebar-border text-left transition-colors"
        >
          <div className="min-w-0">
            <div className="text-sm font-medium truncate">{group.label}</div>
            <div className="text-[11px] text-muted-foreground font-mono truncate">
              {targetLabel}
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              <Chip tone="violet">{group.personaLabel}</Chip>
              <span className="text-[11px] font-mono text-muted-foreground self-center">
                {resolvedConfigId}
              </span>
            </div>
          </div>
          <span className="size-2 rounded-full bg-ready" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-3">
        {nav.map((group) => (
          <div key={group.group} className="px-3 mb-4">
            <div className="text-[11px] text-muted-foreground px-2 mb-1 font-medium">
              {group.group}
            </div>
            <div className="space-y-0.5">
              {group.items.map((it) => {
                const Icon = it.icon;
                const active = pathname === it.to || (it.to !== "/" && pathname.startsWith(it.to));
                return (
                  <Link
                    key={it.to}
                    to={it.to}
                    aria-current={active ? "page" : undefined}
                    className={`flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-all ${
                      active
                        ? "bg-primary/12 text-primary font-medium shadow-[inset_2px_0_0_var(--primary)] pl-[calc(0.5rem-2px)]"
                        : "text-sidebar-foreground/75 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground"
                    }`}
                  >
                    <Icon className="size-4" />
                    <span>{it.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {(liveJob || latest) && (
        <div className="border-t border-sidebar-border p-3">
          {liveJob && (
            <div className="rounded-md border border-info/40 p-2.5 bg-info/5 mb-2">
              <div className="text-[11px] text-info font-medium">Live rehearsal</div>
              <Link
                to="/runner"
                className="mt-0.5 font-mono text-xs text-foreground hover:text-primary block truncate"
              >
                {liveJob.id} · {liveJob.status}
              </Link>
              <div className="text-[11px] text-muted-foreground mt-1">
                {liveJob.runId ? `run ${liveJob.runId}` : "run id when CLI finishes"}
              </div>
            </div>
          )}
          {latest && (
            <div className="rounded-md border border-sidebar-border p-2.5 bg-surface">
              <div className="text-[11px] text-muted-foreground">
                {liveJob ? "Last completed run" : "Latest run"}
              </div>
              <Link
                to="/runs/$runId"
                params={{ runId: latest.id }}
                className="mt-0.5 font-mono text-xs text-foreground hover:text-primary block truncate"
              >
                {latest.id}
              </Link>
              <div className="flex items-center gap-1.5 mt-1.5">
                <span
                  className="size-1.5 rounded-full"
                  style={{ background: `var(--${latest.status})` }}
                />
                <span className="text-[11px] text-muted-foreground">
                  {latest.readiness} · {latest.readinessBand} · {formatRel(latest.startedAt)}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
