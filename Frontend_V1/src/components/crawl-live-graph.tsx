import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api/client";

type NodeStatus = "queued" | "visiting" | "visited" | "skipped" | "error";
type RawNode = { id: string; status: NodeStatus };
type RawEdge = { source: string; target: string };

interface SimNode {
  id: string;
  status: NodeStatus;
  x: number;
  y: number;
  vx: number;
  vy: number;
  label: string;
}

interface SimEdge {
  source: string;
  target: string;
}

const STATUS_COLOR: Record<NodeStatus, string> = {
  visited:  "#3b82f6",
  visiting: "#22c55e",
  queued:   "#6b7280",
  skipped:  "#374151",
  error:    "#ef4444",
};

const STATUS_R: Record<NodeStatus, number> = {
  visited:  7,
  visiting: 10,
  queued:   4,
  skipped:  3,
  error:    7,
};

function pathLabel(url: string): string {
  try {
    const path = new URL(url).pathname;
    const parts = path.split("/").filter(Boolean);
    return parts.length ? "/" + parts.slice(-2).join("/") : "/";
  } catch {
    return url.slice(0, 20);
  }
}

function useForceSimulation(
  rawNodes: RawNode[],
  rawEdges: RawEdge[],
  width: number,
  height: number,
) {
  const nodesRef = useRef<Map<string, SimNode>>(new Map());
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const map = nodesRef.current;

    // Add new nodes; update status of existing ones
    for (const n of rawNodes) {
      if (map.has(n.id)) {
        map.get(n.id)!.status = n.status;
      } else {
        // Spawn near center with slight random offset
        map.set(n.id, {
          id: n.id,
          status: n.status,
          x: width / 2 + (Math.random() - 0.5) * 80,
          y: height / 2 + (Math.random() - 0.5) * 80,
          vx: 0,
          vy: 0,
          label: pathLabel(n.id),
        });
      }
    }
  }, [rawNodes, width, height]);

  useEffect(() => {
    let frame: number;
    const map = nodesRef.current;

    function simulate() {
      const nodes = Array.from(map.values());
      const edgeSet = new Set(rawEdges.map(e => `${e.source}||${e.target}`));

      const alpha = 0.08;
      const repulsion = 1800;
      const springLen = 90;
      const springK = 0.04;
      const damping = 0.85;
      const cx = width / 2, cy = height / 2;

      // Gravity toward center
      for (const n of nodes) {
        n.vx += (cx - n.x) * 0.003;
        n.vy += (cy - n.y) * 0.003;
      }

      // Repulsion between all node pairs
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const dx = b.x - a.x, dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsion / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx * alpha;
          a.vy -= fy * alpha;
          b.vx += fx * alpha;
          b.vy += fy * alpha;
        }
      }

      // Spring attraction along edges
      for (const e of rawEdges) {
        const a = map.get(e.source), b = map.get(e.target);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const stretch = dist - springLen;
        const fx = (dx / dist) * stretch * springK;
        const fy = (dy / dist) * stretch * springK;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }

      // Integrate + damp + clamp to canvas
      const pad = 24;
      for (const n of nodes) {
        n.vx *= damping;
        n.vy *= damping;
        n.x = Math.max(pad, Math.min(width - pad, n.x + n.vx));
        n.y = Math.max(pad, Math.min(height - pad, n.y + n.vy));
      }

      setTick(t => t + 1);
      frame = requestAnimationFrame(simulate);
    }

    frame = requestAnimationFrame(simulate);
    return () => cancelAnimationFrame(frame);
  }, [rawEdges, width, height]);

  return nodesRef.current;
}

interface Props {
  runId: string;
  phase?: string;
  pollingMs?: number;
}

export function CrawlLiveGraph({ runId, phase, pollingMs = 1500 }: Props) {
  const isCrawling = phase === "crawling" || phase === "starting";
  const { data, isLoading, isFetched } = useQuery({
    queryKey: ["crawlGraph", runId],
    queryFn: () => api.crawlGraph(runId),
    refetchInterval: pollingMs > 0 ? pollingMs : false,
    enabled: !!runId,
  });

  const W = 560, H = 360;
  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];
  const simNodes = useForceSimulation(nodes, edges, W, H);
  const nodeArr = Array.from(simNodes.values());

  const visiting = nodes.filter(n => n.status === "visiting").length;
  const visited  = nodes.filter(n => n.status === "visited").length;
  const queued   = nodes.filter(n => n.status === "queued").length;
  const skipped  = nodes.filter(n => n.status === "skipped").length;

  return (
    <div className="space-y-2">
      {/* Legend + stats */}
      <div className="flex flex-wrap items-center gap-4 text-[11px] text-muted-foreground px-1">
        {(["visited","visiting","queued","skipped","error"] as NodeStatus[]).map(s => (
          <span key={s} className="flex items-center gap-1">
            <span className="inline-block rounded-full w-2 h-2" style={{ background: STATUS_COLOR[s] }} />
            {s}
          </span>
        ))}
        <span className="ml-auto font-mono">
          {visited} visited · {visiting > 0 ? `${visiting} active · ` : ""}{queued} queued{skipped > 0 ? ` · ${skipped} skipped` : ""}
          {data?.maxPages ? ` / ${data.maxPages}` : ""}
        </span>
      </div>

      {/* Graph canvas */}
      <div className="rounded-md border border-border bg-surface/60 overflow-hidden">
        {nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-36 gap-2 text-xs text-muted-foreground px-4 text-center">
            {isLoading || (!isFetched && !!runId)
              ? <><Loader2 className="size-4 animate-spin" /> Loading crawl graph…</>
              : isCrawling
                ? <><Loader2 className="size-4 animate-spin" /> Crawl in progress — graph appears as pages are visited</>
                : <>
                    No crawl graph data.
                    <span className="text-[10px]">Restart the server to enable the crawl graph endpoint, or this run had no crawl phase.</span>
                  </>
            }
          </div>
        ) : (
          <svg width={W} height={H} className="block">
            {/* Edges */}
            <g opacity={0.35}>
              {edges.map((e, i) => {
                const a = simNodes.get(e.source), b = simNodes.get(e.target);
                if (!a || !b) return null;
                return (
                  <line
                    key={i}
                    x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke="#6b7280" strokeWidth={1}
                  />
                );
              })}
            </g>
            {/* Nodes */}
            {nodeArr.map(n => {
              const r = STATUS_R[n.status];
              const color = STATUS_COLOR[n.status];
              const isActive = n.status === "visiting";
              return (
                <g key={n.id} transform={`translate(${n.x},${n.y})`}>
                  {isActive && (
                    <circle r={r + 6} fill={color} opacity={0.2}>
                      <animate attributeName="r" values={`${r+4};${r+10};${r+4}`} dur="1.2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.3;0.05;0.3" dur="1.2s" repeatCount="indefinite" />
                    </circle>
                  )}
                  <circle r={r} fill={color} stroke={isActive ? "#fff" : "none"} strokeWidth={isActive ? 1.5 : 0} />
                  {(n.status === "visited" || n.status === "visiting") && (
                    <text
                      y={r + 10}
                      textAnchor="middle"
                      fontSize={9}
                      fill="#9ca3af"
                      fontFamily="monospace"
                    >
                      {n.label}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}
