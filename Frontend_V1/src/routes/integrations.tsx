import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useIntegrations } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";
import { Github, Slack, MessageSquare, Activity, Lock, Users, Webhook } from "lucide-react";

export const Route = createFileRoute("/integrations")({
  head: () => ({ meta: [{ title: "Integrations — Launch Rehearsal" }] }),
  component: IntegrationsPage,
});

const icons: Record<string, typeof Github> = {
  int_gh: Github,
  int_vercel: Webhook,
  int_slack: Slack,
  int_linear: MessageSquare,
  int_jira: MessageSquare,
  int_dd: Activity,
  int_sso: Lock,
  int_rbac: Users,
};

function IntegrationsPage() {
  const { data: integrations = [] } = useIntegrations();
  return (
    <div>
      <PageHeader
        eyebrow="configure"
        title="Integrations"
        description="Enterprise plumbing — wire rehearsal into CI, deploy hooks, alerts, and issue export."
      />
      <div className="p-8 max-w-[1400px] grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrations.map((it) => {
          const Icon = icons[it.id] ?? Github;
          const tone =
            it.status === "connected" ? "ready" : it.status === "phase 2" ? "violet" : "neutral";
          return (
            <Panel
              key={it.id}
              className="p-5 flex items-center justify-between hover:border-border-strong transition-colors gap-4"
            >
              <div className="flex items-center gap-4 min-w-0">
                <div className="size-11 rounded-lg bg-surface-2 border border-border flex items-center justify-center shrink-0">
                  <Icon className="size-5" />
                </div>
                <div className="min-w-0">
                  <div className="font-display font-semibold">{it.name}</div>
                  <div className="text-xs text-muted-foreground">{it.desc}</div>
                  <Chip tone="neutral">{it.category}</Chip>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Chip tone={tone}>{it.status}</Chip>
                <VisionOnly section="integrations.connectButtons">
                <button
                  type="button"
                  className="text-xs font-mono px-3 py-1.5 rounded border border-border hover:bg-surface-2"
                >
                  {it.status === "connected" ? "manage" : "connect"}
                </button>
                </VisionOnly>
              </div>
            </Panel>
          );
        })}
      </div>
    </div>
  );
}
