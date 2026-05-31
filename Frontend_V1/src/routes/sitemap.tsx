import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useLatestRun, useRunBundle, useRunSummaries } from "@/lib/api/hooks";
import { api } from "@/lib/api/client";
import { Filter, GitCompare, Camera } from "lucide-react";

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

function SiteMap() {
  const latest = useLatestRun();
  const { data: runSummaries = [] } = useRunSummaries();
  const [selectedRun, setSelectedRun] = useState(latest?.id ?? "");
  const { data: bundle } = useRunBundle(selectedRun || latest?.id || "");
  if (!bundle) return null;
  const pages = bundle.sitemapPages;
  const edges = bundle.sitemapEdges;

  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");

  const filtered = pages.filter((p) => {
    if (filter === "all") return true;
    if (filter === "errors") return p.errors > 0;
    return p.type === filter;
  });

  const positions: Record<string, [number, number]> = {};
  pages.forEach((p, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    positions[p.id] = [80 + col * 130, 60 + row * 90];
  });

  return (
    <div>
      <PageHeader
        eyebrow="map · pages"
        title="Site map explorer"
        description="Same-origin BFS crawl from latest run. Hubs, leaves, orphans, auth-gated — mirrors sitemap.json + sitemap.md from CLI."
        actions={
          <div className="flex gap-2 flex-wrap">
            <select value={selectedRun} onChange={(e) => setSelectedRun(e.target.value)} className="text-xs bg-surface border border-border rounded-md px-2 py-1 font-mono">
              {runSummaries.filter((r) => r.pages > 0).map((r) => <option key={r.id} value={r.id}>{r.id}</option>)}
            </select>
            <Link to="/compare" search={{ a: runSummaries[1]?.id, b: latest.id }} className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5">
              <GitCompare className="size-3.5" /> diff sitemap
            </Link>
          </div>
        }
      />
      <div className="p-8 max-w-[1400px] grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel className="lg:col-span-2 p-6">
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <Filter className="size-3.5 text-muted-foreground" />
            {FILTERS.map((f) => (
              <button key={f} type="button" onClick={() => setFilter(f)} className={`text-[11px] px-2 py-0.5 rounded border ${filter === f ? "border-primary text-primary bg-primary/10" : "border-border text-muted-foreground"}`}>
                {f}
              </button>
            ))}
          </div>
          <div className="relative h-[440px] grid-bg rounded-lg border border-border overflow-hidden">
            <svg viewBox="0 0 600 440" className="absolute inset-0 w-full h-full">
              {edges.map((edge, i) => {
                const [x1, y1] = positions[edge.from] ?? [0, 0];
                const [x2, y2] = positions[edge.to] ?? [0, 0];
                return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--border-strong)" strokeWidth="1" />;
              })}
              {filtered.map((p) => {
                const [x, y] = positions[p.id] ?? [0, 0];
                const r = p.type === "hub" ? 12 : 8;
                return (
                  <g key={p.id}>
                    <circle cx={x} cy={y} r={r} fill={typeColor[p.type]} fillOpacity="0.18" stroke={typeColor[p.type]} strokeWidth="1.5" />
                    <text x={x} y={y + r + 14} textAnchor="middle" className="fill-foreground font-mono" fontSize="10">{p.path}</text>
                  </g>
                );
              })}
            </svg>
          </div>
          <div className="mt-4 flex items-center gap-3 text-[11px] font-mono flex-wrap">
            {Object.entries(typeColor).map(([k, v]) => (
              <span key={k} className="inline-flex items-center gap-1.5"><span className="size-2.5 rounded-full" style={{ background: v, opacity: 0.7 }} />{k}</span>
            ))}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-4 border-b border-border">
            <div className="text-xs text-muted-foreground">All pages · {selectedRun}</div>
            <div className="font-display text-base font-semibold mt-0.5">{filtered.length} shown</div>
          </div>
          <div className="divide-y divide-border max-h-[460px] overflow-y-auto">
            {filtered.map((p) => (
              <div key={p.id} className="p-3 hover:bg-surface-2/40">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs">{p.path}</span>
                  <Chip tone={p.type === "orphan" ? "warn" : p.type === "auth" ? "violet" : "neutral"}>{p.type}</Chip>
                </div>
                <div className="text-[11px] text-muted-foreground mt-0.5">{p.title}{p.workflow ? ` · ${p.workflow}` : ""}{p.errors ? ` · ${p.errors} err` : ""}</div>
                <button type="button" className="mt-1 text-[10px] text-primary inline-flex items-center gap-1"><Camera className="size-3" /> preview screenshot</button>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
