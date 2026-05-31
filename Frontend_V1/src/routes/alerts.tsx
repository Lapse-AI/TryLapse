import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useAlerts } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";
import { Slack, Mail, Webhook, Bell as BellIcon } from "lucide-react";

export const Route = createFileRoute("/alerts")({
  head: () => ({ meta: [{ title: "Alerts — Launch Rehearsal" }] }),
  component: Alerts,
});

const iconFor = { slack: Slack, email: Mail, webhook: Webhook };

const recent = [
  {
    when: "14m ago",
    title: "P0 surfaced: SSO callback drops session on Safari 17",
    env: "prod-canary",
    tone: "danger" as const,
  },
  { when: "6h ago", title: "Readiness dropped 74 → 68", env: "staging", tone: "warn" as const },
  {
    when: "yesterday",
    title: "Recurring blocker: Auth wall Argyle (2nd run)",
    env: "staging",
    tone: "danger" as const,
  },
  {
    when: "2d ago",
    title: "New delight: code samples copy as runnable cURL",
    env: "staging",
    tone: "ready" as const,
  },
];

function Alerts() {
  const { data: alertChannels = [] } = useAlerts();
  return (
    <div>
      <PageHeader
        eyebrow="monitor"
        title="Alerts & notifications"
        description="Route readiness drops, P0 events, and weekly digests to the channels your team already lives in."
      />
      <div className="p-8 max-w-[1400px] grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Panel className="lg:col-span-2 overflow-hidden">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div>
              <div className="text-xs text-muted-foreground">Channels</div>
              <div className="font-display text-lg font-semibold mt-0.5">
                {alertChannels.length} configured
              </div>
            </div>
            <VisionOnly section="alerts.addChannel">
              <button
                type="button"
                className="text-xs font-mono px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90"
              >
                + add channel
              </button>
            </VisionOnly>
          </div>
          <div className="divide-y divide-border">
            {alertChannels.map((c) => {
              const Icon = iconFor[c.kind];
              return (
                <div
                  key={c.id}
                  className="p-4 flex items-center justify-between hover:bg-surface-2/30"
                >
                  <div className="flex items-center gap-3">
                    <div className="size-9 rounded-md bg-surface-2 border border-border flex items-center justify-center">
                      <Icon className="size-4" />
                    </div>
                    <div>
                      <div className="font-medium text-sm">{c.name}</div>
                      <div className="text-[11px] text-muted-foreground font-mono">{c.trigger}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Chip tone={c.enabled ? "ready" : "neutral"}>{c.enabled ? "on" : "off"}</Chip>
                    <Chip>{c.kind}</Chip>
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        <VisionOnly section="alerts.recentFeed">
          <Panel className="overflow-hidden">
            <div className="p-4 border-b border-border flex items-center gap-2">
              <BellIcon className="size-4 text-primary" />
              <div className="font-display font-semibold">Recent alerts</div>
            </div>
            <div className="divide-y divide-border">
              {recent.map((r, i) => (
                <div key={i} className="p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Chip tone={r.tone}>{r.env}</Chip>
                    <span className="text-[11px] text-muted-foreground font-mono">{r.when}</span>
                  </div>
                  <div className="text-sm">{r.title}</div>
                </div>
              ))}
            </div>
          </Panel>
        </VisionOnly>
      </div>
    </div>
  );
}
