import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, UnderConstruction } from "@/components/ui-bits";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { useLatestRun, useRunBundle, useRunSummaries, useConfigs } from "@/lib/api/hooks";
import { api, artifactUrl } from "@/lib/api/client";
import { Filter, GitCompare, Camera, Plus } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/sitemap")({
  head: () => ({ meta: [{ title: "Site map — Launch Rehearsal" }] }),
  component: SiteMap,
});

const typeColor: Record<string, string> = {
  hub: "var(--primary)",
  leaf: "var(--info)",
  orphan: "var(--warn)",
  auth: "var(--violet)",
};

const FILTERS = ["all", "hub", "leaf", "orphan", "auth", "errors"] as const;

function screenshotForPath(
  bundle: NonNullable<ReturnType<typeof useRunBundle>["data"]>,
  pagePath: string,
): string | undefined {
  const page = bundle.sitemapPages.find((p) => p.path === pagePath);
  if (page?.screenshotPath) return page.screenshotPath;
  const step = bundle.steps.find((s) => {
    const u = s.finalUrl || s.requestedUrl || "";
    try {
      const pathname = new URL(u, "http://local").pathname;
      return pathname === pagePath || u.includes(pagePath);
    } catch {
      return u.includes(pagePath);
    }
  });
  const fromStep = step?.artifactPaths?.find((p) => p.endsWith(".png"));
  if (fromStep) return fromStep;
  const shot = bundle.screenshots.find(
    (s) => s.label.includes(pagePath) || s.path.includes(pagePath.replace(/\//g, "_")),
  );
  return shot?.path;
}

function SiteMap() {
  const latest = useLatestRun();
  const { data: runSummaries = [] } = useRunSummaries();
  const { data: configs = [] } = useConfigs();
  const [selectedRun, setSelectedRun] = useState(latest?.id ?? "");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const { configId, pickConfig } = usePersistedConfigId();
  const [appendPending, setAppendPending] = useState(false);
  const { data: bundle } = useRunBundle(selectedRun || latest?.id || "");
  const configOptions = useMemo(
    () => (configs.length ? configs : [{ id: "lr-self", name: "lr-self" }]),
    [configs],
  );

  if (!bundle) return null;
  const pages = bundle.sitemapPages;
  const edges = bundle.sitemapEdges;

  const filtered = pages.filter((p) => {
    if (filter === "all") return true;
    if (filter === "errors") return p.errors > 0;
    return p.type === filter;
  });

  const selectedPage = selectedPageId ? pages.find((p) => p.id === selectedPageId) : filtered[0];
  const previewPath = selectedPage ? screenshotForPath(bundle, selectedPage.path) : undefined;

  const positions: Record<string, [number, number]> = {};
  pages.forEach((p, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    positions[p.id] = [80 + col * 130, 60 + row * 90];
  });

  const appendJourney = async (path: string, title?: string) => {
    setAppendPending(true);
    try {
      const out = await api.appendJourneyToConfig({ configId, path, title });
      toast.success(`Added ${out.journeyId} — edit on Config (YAML), then Run in Runner`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not append journey");
    } finally {
      setAppendPending(false);
    }
  };

  return (
    <UnderConstruction>
    <div>
      <PageHeader
        eyebrow="map · pages"
        title="Site map explorer"
        description="BFS crawl from a run. Preview a page, then add a smoke navigate journey to your YAML config."
        actions={
          <div className="flex gap-2 flex-wrap items-center">
            <select
              value={selectedRun}
              onChange={(e) => setSelectedRun(e.target.value)}
              className="text-xs bg-surface border border-border rounded-md px-2 py-1 font-mono"
            >
              {runSummaries
                .filter((r) => r.pages > 0)
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.id}
                  </option>
                ))}
            </select>
            <select
              value={configId}
              onChange={(e) => pickConfig(e.target.value)}
              className="text-xs bg-surface border border-border rounded-md px-2 py-1 font-mono"
              title="Target config for new journeys"
            >
              {configOptions.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id}
                </option>
              ))}
            </select>
            <Link
              to="/compare"
              search={{ a: runSummaries[1]?.id, b: latest?.id }}
              className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
            >
              <GitCompare className="size-3.5" /> diff sitemap
            </Link>
            <Link
              to="/config"
              className="text-xs font-mono px-3 py-1.5 rounded-md border border-primary/40 text-primary hover:bg-primary/10"
            >
              Config (YAML)
            </Link>
          </div>
        }
      />
      <div className="p-8 max-w-[1400px] grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel className="lg:col-span-2 p-6 space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="size-3.5 text-muted-foreground" />
            {FILTERS.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`text-[11px] px-2 py-0.5 rounded border ${filter === f ? "border-primary text-primary bg-primary/10" : "border-border text-muted-foreground"}`}
              >
                {f}
              </button>
            ))}
          </div>
          <div className="relative h-[440px] grid-bg rounded-lg border border-border overflow-hidden">
            <svg viewBox="0 0 600 440" className="absolute inset-0 w-full h-full">
              {edges.map((edge, i) => {
                const [x1, y1] = positions[edge.from] ?? [0, 0];
                const [x2, y2] = positions[edge.to] ?? [0, 0];
                return (
                  <line
                    key={i}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="var(--border-strong)"
                    strokeWidth="1"
                  />
                );
              })}
              {filtered.map((p) => {
                const [x, y] = positions[p.id] ?? [0, 0];
                const r = p.type === "hub" ? 12 : 8;
                const active = selectedPage?.id === p.id;
                return (
                  <g key={p.id} className="cursor-pointer" onClick={() => setSelectedPageId(p.id)}>
                    <circle
                      cx={x}
                      cy={y}
                      r={r}
                      fill={typeColor[p.type]}
                      fillOpacity={active ? 0.45 : 0.18}
                      stroke={typeColor[p.type]}
                      strokeWidth={active ? 2.5 : 1.5}
                    />
                    <text
                      x={x}
                      y={y + r + 14}
                      textAnchor="middle"
                      className="fill-foreground font-mono"
                      fontSize="10"
                    >
                      {p.path}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
          {selectedPage && (
            <Panel className="p-4 border border-border bg-surface-2/30">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-sm">{selectedPage.path}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{selectedPage.title}</div>
                </div>
                <button
                  type="button"
                  disabled={appendPending}
                  onClick={() => void appendJourney(selectedPage.path, selectedPage.title)}
                  className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground inline-flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Plus className="size-3.5" />
                  Add navigate journey to {configId}
                </button>
              </div>
              {previewPath ? (
                <img
                  src={artifactUrl(previewPath)}
                  alt={`Screenshot ${selectedPage.path}`}
                  className="mt-3 w-full max-h-[280px] object-contain rounded-md border border-border bg-surface"
                />
              ) : (
                <p className="mt-3 text-xs text-muted-foreground">
                  No screenshot for this path in run {selectedRun}. Re-run with crawl or a journey
                  that visits this URL.
                </p>
              )}
            </Panel>
          )}
          <div className="flex items-center gap-3 text-[11px] font-mono flex-wrap">
            {Object.entries(typeColor).map(([k, v]) => (
              <span key={k} className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-full" style={{ background: v, opacity: 0.7 }} />
                {k}
              </span>
            ))}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-4 border-b border-border">
            <div className="text-xs text-muted-foreground">All pages · {selectedRun}</div>
            <div className="font-display text-base font-semibold mt-0.5">
              {filtered.length} shown
            </div>
          </div>
          <div className="divide-y divide-border max-h-[460px] overflow-y-auto">
            {filtered.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedPageId(p.id)}
                className={`w-full text-left p-3 hover:bg-surface-2/40 ${selectedPage?.id === p.id ? "bg-primary/5" : ""}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs">{p.path}</span>
                  <Chip
                    tone={p.type === "orphan" ? "warn" : p.type === "auth" ? "violet" : "neutral"}
                  >
                    {p.type}
                  </Chip>
                </div>
                <div className="text-[11px] text-muted-foreground mt-0.5">
                  {p.title}
                  {p.workflow ? ` · ${p.workflow}` : ""}
                  {p.errors ? ` · ${p.errors} err` : ""}
                </div>
                <span className="mt-1 text-[11px] text-primary inline-flex items-center gap-1">
                  <Camera className="size-3" /> preview
                </span>
              </button>
            ))}
          </div>
        </Panel>
      </div>
    </div>
    </UnderConstruction>
  );
}
