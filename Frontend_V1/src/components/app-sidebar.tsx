import { useState, useEffect } from "react";
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
  LogOut,
  HardHat,
  User,
  ShieldAlert,
} from "lucide-react";
import { formatRel } from "@/lib/mock-data";
import { useLatestRun, useWorkspace, useScopedActiveJobs, useAuthMe } from "@/lib/api/hooks";
import { useTestGroup, displayTargetForGroup } from "@/hooks/use-test-group";
import { Chip } from "@/components/ui-bits";
import { getWorkspace } from "@/lib/workspace";
import { signOut } from "@/lib/test-auth";
import { clearWorkspace } from "@/lib/workspace";

const nav = [
  {
    group: "Monitor",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard },
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
      { to: "/init", label: "Setup", icon: Wand2 },
      { to: "/library", label: "Journeys", icon: BookOpen },
      { to: "/config", label: "Config", icon: Settings },
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
  { group: "Agents", items: [{ to: "/agents", label: "Agents", icon: Bot }] },
  {
    group: "Platform",
    items: [
      { to: "/integrations", label: "Integrations", icon: Plug },
      { to: "/cli", label: "CLI", icon: Terminal },
    ],
  },
];

const workspaceNav = [
  {
    group: "Run",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard },
      { to: "/runs", label: "Runs", icon: Activity },
      { to: "/compare", label: "Compare", icon: GitCompare },
    ],
  },
  {
    group: "Analyze",
    items: [
      { to: "/trends", label: "Trends", icon: TrendingUp },
      { to: "/alerts", label: "Alerts", icon: Bell, wip: true },
    ],
  },
  {
    group: "Build",
    items: [
      { to: "/config", label: "Config", icon: Settings },
      { to: "/runner", label: "Runner", icon: PlayCircle },
      { to: "/personas", label: "Personas", icon: User },
      { to: "/library", label: "Journeys", icon: BookOpen, wip: true },
      { to: "/agents", label: "Agents", icon: Bot, wip: true },
    ],
  },
  {
    group: "Platform",
    items: [
      { to: "/integrations", label: "Integrations", icon: Plug, wip: true },
      { to: "/settings", label: "Settings", icon: Settings },
      { to: "/admin", label: "Company", icon: ShieldAlert },
    ],
  },
  {
    group: "Coming soon",
    items: [
      { to: "/recommendations", label: "Recommendations", icon: Lightbulb, wip: true },
      { to: "/sitemap", label: "Site map", icon: Network, wip: true },
      { to: "/workflows", label: "Workflows", icon: GitBranch, wip: true },
      { to: "/cli", label: "CLI", icon: Terminal, wip: true },
    ],
  },
];

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const latest = useLatestRun();
  const { data: activeJobs = [] } = useScopedActiveJobs();
  const liveJob = activeJobs[0];
  const { data: workspace } = useWorkspace();
  const { data: me } = useAuthMe();
  const { group, resolvedConfigId } = useTestGroup();
  const targetLabel = displayTargetForGroup(group);
  // Start null to match server render, then populate from localStorage after mount
  const [userWorkspace, setUserWorkspace] = useState<ReturnType<typeof getWorkspace>>(null);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setUserWorkspace(getWorkspace());
    setMounted(true);
  }, []);

  const handleSignOut = () => {
    signOut();
    clearWorkspace();
    window.location.href = "/signin";
  };

  // Dashboard link: use workspace-scoped URL when available
  const dashboardTo = userWorkspace ? (`/$workspaceSlug/dashboard` as const) : ("/runs" as const);
  const dashboardParams = userWorkspace ? { workspaceSlug: userWorkspace.slug } : undefined;

  // Resolve the actual href for a nav item — workspace-scope all items when workspace is active
  const resolveHref = (to: string): string => {
    if (!userWorkspace) return to;
    if (to === "/") return `/${userWorkspace.slug}/dashboard`;
    return `/${userWorkspace.slug}${to}`;
  };

  return (
    <aside
      className="w-60 h-full shrink-0 border-r border-sidebar-border text-sidebar-foreground flex flex-col overflow-hidden"
      style={{ background: "var(--sidebar)" }}
    >
      <div className="px-4 h-14 flex items-center gap-2.5 border-b border-sidebar-border/70">
        <div className="size-7 rounded-lg bg-primary/15 border border-primary/25 flex items-center justify-center shadow-[0_1px_3px_color-mix(in_oklab,var(--primary)_20%,transparent)]">
          <ShieldCheck className="size-4 text-primary" />
        </div>
        <div className="leading-tight">
          <div className="font-display font-semibold text-[15px] tracking-tight">TryLapse</div>
          <div className="text-[11px] text-muted-foreground">
            <span className="px-1 py-px rounded bg-surface-2 border border-border text-[11px] font-mono">
              Monitor
            </span>
          </div>
        </div>
      </div>

      {/* Workspace header */}
      <div className="px-3 py-3 border-b border-sidebar-border">
        <div className="w-full flex items-center justify-between px-2.5 py-2 rounded-md bg-sidebar-accent border border-sidebar-border">
          <div className="min-w-0">
            <div className="text-sm font-medium truncate" suppressHydrationWarning>
              {userWorkspace?.name ?? workspace?.name ?? group.label}
            </div>
            <div
              className="text-[11px] text-muted-foreground font-mono truncate"
              suppressHydrationWarning
            >
              {userWorkspace ? `/${userWorkspace.slug}` : targetLabel}
            </div>
            {userWorkspace && (
              <div className="mt-1">
                {/* Signed-in user's identity, not the frozen onboarding role —
                    a teammate who joins later must see their own name here,
                    not whatever the workspace creator picked once. */}
                <Chip tone="violet">{me?.name ?? userWorkspace.teamRole}</Chip>
              </div>
            )}
            {!userWorkspace && (
              <div className="mt-1 flex flex-wrap gap-1">
                <Chip tone="violet">{group.personaLabel}</Chip>
                <span className="text-[11px] font-mono text-muted-foreground self-center">
                  {resolvedConfigId}
                </span>
              </div>
            )}
          </div>
          <span className="size-2 rounded-full bg-ready" />
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-3">
        {(userWorkspace ? workspaceNav : nav).map((navGroup) => (
          <div key={navGroup.group} className="px-3 mb-4">
            <div className="text-[11px] text-muted-foreground px-2 mb-1 font-medium">
              {navGroup.group}
            </div>
            <div className="space-y-0.5">
              {navGroup.items.map((it) => {
                const Icon = it.icon;
                const linkClassName = (active: boolean) =>
                  `flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-all ${
                    active
                      ? "bg-primary/12 text-primary font-medium shadow-[inset_2px_0_0_var(--primary)] pl-[calc(0.5rem-2px)]"
                      : "text-sidebar-foreground/75 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground"
                  }`;

                // Dashboard — always workspace-scoped
                if (it.to === "/") {
                  const wsPath = userWorkspace ? `/${userWorkspace.slug}/dashboard` : "/runs";
                  const active = pathname === wsPath;
                  if (userWorkspace) {
                    return (
                      <Link
                        key={it.to}
                        to="/$workspaceSlug/dashboard"
                        params={{ workspaceSlug: userWorkspace.slug }}
                        aria-current={active ? "page" : undefined}
                        className={linkClassName(active)}
                      >
                        <Icon className="size-4" />
                        <span>{it.label}</span>
                      </Link>
                    );
                  }
                  return (
                    <Link
                      key={it.to}
                      to="/runs"
                      aria-current={active ? "page" : undefined}
                      className={linkClassName(active)}
                    >
                      <Icon className="size-4" />
                      <span>{it.label}</span>
                    </Link>
                  );
                }

                // Runs — workspace-scoped when workspace exists
                if (it.to === "/runs" && userWorkspace) {
                  const wsPath = `/${userWorkspace.slug}/runs`;
                  const active = pathname === wsPath || pathname.startsWith(wsPath);
                  return (
                    <Link
                      key={it.to}
                      to="/$workspaceSlug/runs"
                      params={{ workspaceSlug: userWorkspace.slug }}
                      search={{ page: 1 }}
                      aria-current={active ? "page" : undefined}
                      className={linkClassName(active)}
                    >
                      <Icon className="size-4" />
                      <span>{it.label}</span>
                    </Link>
                  );
                }

                // Admin — never workspace-scoped, it spans every workspace
                if (it.to === "/admin") {
                  const active = pathname === "/admin";
                  return (
                    <Link
                      key={it.to}
                      to="/admin"
                      aria-current={active ? "page" : undefined}
                      className={linkClassName(active)}
                    >
                      <Icon className="size-4" />
                      <span>{it.label}</span>
                    </Link>
                  );
                }

                // All other routes — workspace-scoped when workspace is active
                const href = resolveHref(it.to);
                const active = pathname === href || (it.to !== "/" && pathname.startsWith(href));
                return (
                  <Link
                    key={it.to}
                    to={href}
                    aria-current={active ? "page" : undefined}
                    className={linkClassName(active)}
                  >
                    <Icon className="size-4 shrink-0" />
                    <span className="flex-1 truncate">{it.label}</span>
                    {"wip" in it && !!(it as { wip?: boolean }).wip && (
                      <HardHat className="size-3.5 text-warn/70 shrink-0" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {mounted && (liveJob || latest) && (
        <div className="border-t border-sidebar-border p-3">
          {liveJob && (
            <div className="rounded-md border border-info/40 p-2.5 bg-info/5 mb-2">
              <div className="text-[11px] text-info font-medium">Live rehearsal</div>
              {userWorkspace ? (
                <Link
                  to="/$workspaceSlug/runner"
                  params={{ workspaceSlug: userWorkspace.slug }}
                  className="mt-0.5 font-mono text-xs text-foreground hover:text-primary block truncate"
                >
                  {liveJob.id} · {liveJob.status}
                </Link>
              ) : (
                <Link
                  to="/runner"
                  className="mt-0.5 font-mono text-xs text-foreground hover:text-primary block truncate"
                >
                  {liveJob.id} · {liveJob.status}
                </Link>
              )}
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

      {/* Sign-out */}
      <div className="border-t border-sidebar-border p-3">
        <button
          type="button"
          onClick={handleSignOut}
          className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/70 transition-all"
        >
          <LogOut className="size-4" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
