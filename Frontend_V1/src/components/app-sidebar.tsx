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
import { useLatestRun, useWorkspace } from "@/lib/api/hooks";

const nav = [
  {
    group: "Monitor",
    items: [
      { to: "/", label: "Command center", icon: LayoutDashboard },
      { to: "/runs", label: "Runs", icon: Activity },
      { to: "/runner", label: "Runner", icon: PlayCircle },
      { to: "/compare", label: "Compare runs", icon: GitCompare },
      { to: "/trends", label: "Trends", icon: TrendingUp },
      { to: "/alerts", label: "Alerts", icon: Bell },
      { to: "/recommendations", label: "Recommendations", icon: Lightbulb },
    ],
  },
  {
    group: "Map",
    items: [
      { to: "/sitemap", label: "Site map", icon: Network },
      { to: "/workflows", label: "Workflows", icon: GitBranch },
      { to: "/library", label: "Journey library", icon: BookOpen },
    ],
  },
  { group: "Agents", items: [{ to: "/agents", label: "Agent control", icon: Bot }] },
  {
    group: "Configure",
    items: [
      { to: "/init", label: "Init wizard", icon: Wand2 },
      { to: "/config", label: "Workspace", icon: Settings },
      { to: "/integrations", label: "Integrations", icon: Plug },
      { to: "/cli", label: "CLI", icon: Terminal },
    ],
  },
];

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const latest = useLatestRun();
  const { data: workspace } = useWorkspace();

  return (
    <aside className="w-60 shrink-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground flex flex-col">
      <div className="px-4 h-14 flex items-center gap-2.5 border-b border-sidebar-border">
        <div className="size-7 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center">
          <ShieldCheck className="size-4 text-primary" />
        </div>
        <div className="leading-tight">
          <div className="font-display font-semibold text-[15px] tracking-tight">Rehearsal</div>
          <div className="text-[11px] text-muted-foreground">Monitor</div>
        </div>
      </div>

      <div className="px-3 py-3 border-b border-sidebar-border">
        <button className="w-full flex items-center justify-between px-2.5 py-2 rounded-md bg-sidebar-accent hover:bg-sidebar-accent/70 border border-sidebar-border text-left transition-colors">
          <div>
            <div className="text-sm font-medium">{workspace?.name ?? "Workspace"}</div>
            <div className="text-[11px] text-muted-foreground font-mono truncate">
              {workspace?.targetUrl?.replace(/^https?:\/\//, "") ?? "—"}
            </div>
          </div>
          <span className="size-2 rounded-full bg-ready pulse-dot" />
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
                    className={`flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-colors ${
                      active
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground"
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

      {latest && (
        <div className="border-t border-sidebar-border p-3">
          <div className="rounded-md border border-sidebar-border p-2.5 bg-surface">
            <div className="text-[11px] text-muted-foreground">Latest run</div>
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
        </div>
      )}
    </aside>
  );
}
