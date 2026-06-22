import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Network } from "lucide-react";
import { api } from "@/lib/api/client";

type NodeStatus = "queued" | "visiting" | "visited" | "skipped" | "error";
type RawNode = { id: string; status: NodeStatus };
type RawEdge = { source: string; target: string };

const STATUS_COLOR: Record<NodeStatus, string> = {
  visited: "#3b82f6",
  visiting: "#22c55e",
  queued: "#6b7280",
  skipped: "#374151",
  error: "#ef4444",
};

function pathLabel(url: string): string {
  try {
    const path = new URL(url).pathname;
    const parts = path.split("/").filter(Boolean);
    return parts.length ? "/" + parts.slice(-2).join("/") : "/";
  } catch {
    return url.slice(0, 24);
  }
}

interface LayoutNode {
  id: string;
  status: NodeStatus;
  label: string;
  depth: number;
  x: number;
  y: number;
  parentId: string | null;
  isRoot: boolean;
}

const ROW_HEIGHT = 78;
const SLOT_WIDTH = 110;
const TOP_PAD = 36;
const SIDE_PAD = 60;

/**
 * Deterministic tree layout: one entrance node at the root, BFS depth on the Y
 * axis, children fanned out under their parent on the X axis. Nodes reachable
 * by more than one path keep only their first-discovered parent so the result
 * is a strict tree, not a tangled graph — this is what makes "one peak
 * entrance node with branches underneath" legible at a glance.
 */
function layoutTree(rawNodes: RawNode[], rawEdges: RawEdge[], rootId: string | null) {
  const nodeById = new Map(rawNodes.map((n) => [n.id, n]));
  const childrenBySource = new Map<string, string[]>();
  for (const e of rawEdges) {
    if (!childrenBySource.has(e.source)) childrenBySource.set(e.source, []);
    childrenBySource.get(e.source)!.push(e.target);
  }

  const root = rootId && nodeById.has(rootId) ? rootId : (rawNodes[0]?.id ?? null);
  if (!root) return { tree: [] as LayoutNode[], orphans: [] as RawNode[], width: 0, height: 0 };

  const depthOf = new Map<string, number>([[root, 0]]);
  const parentOf = new Map<string, string | null>([[root, null]]);
  const treeChildren = new Map<string, string[]>();
  const queue: string[] = [root];

  while (queue.length) {
    const current = queue.shift()!;
    const depth = depthOf.get(current)!;
    for (const childId of childrenBySource.get(current) ?? []) {
      if (depthOf.has(childId) || !nodeById.has(childId)) continue; // already placed, or unknown node
      depthOf.set(childId, depth + 1);
      parentOf.set(childId, current);
      if (!treeChildren.has(current)) treeChildren.set(current, []);
      treeChildren.get(current)!.push(childId);
      queue.push(childId);
    }
  }

  // Assign x via post-order leaf counting so parents center over their children.
  const xOf = new Map<string, number>();
  let nextLeafSlot = 0;
  function place(id: string): number {
    const kids = treeChildren.get(id) ?? [];
    if (kids.length === 0) {
      const x = nextLeafSlot * SLOT_WIDTH + SIDE_PAD;
      nextLeafSlot += 1;
      xOf.set(id, x);
      return x;
    }
    const childXs = kids.map(place);
    const x = (Math.min(...childXs) + Math.max(...childXs)) / 2;
    xOf.set(id, x);
    return x;
  }
  place(root);

  const tree: LayoutNode[] = [];
  for (const [id, depth] of depthOf) {
    const raw = nodeById.get(id)!;
    tree.push({
      id,
      status: raw.status,
      label: id === root ? pathLabel(id) || "/" : pathLabel(id),
      depth,
      x: xOf.get(id) ?? SIDE_PAD,
      y: depth * ROW_HEIGHT + TOP_PAD,
      parentId: parentOf.get(id) ?? null,
      isRoot: id === root,
    });
  }

  const orphans = rawNodes.filter((n) => !depthOf.has(n.id));
  const width = Math.max(nextLeafSlot * SLOT_WIDTH + SIDE_PAD * 2, 360);
  const height = (Math.max(...Array.from(depthOf.values()), 0) + 1) * ROW_HEIGHT + TOP_PAD + 30;

  return { tree, orphans, width, height };
}

interface Props {
  configId?: string | null;
  /** Pass when the run already finished — fetches from /api/runs/{id}/crawl-graph instead. */
  runId?: string | null;
}

export function CrawlTreeGraph({ configId, runId }: Props) {
  const queryKey = runId
    ? ["crawlGraphTree", "run", runId]
    : ["crawlGraphTree", "product", configId];
  const { data, isLoading, error } = useQuery({
    queryKey,
    queryFn: () => (runId ? api.crawlGraph(runId) : api.productCrawlGraph(configId!)),
    enabled: !!(runId || configId),
  });

  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];
  const { tree, orphans, width, height } = useMemo(
    () => layoutTree(nodes, edges, data?.targetUrl ?? null),
    [nodes, edges, data?.targetUrl],
  );

  if (!configId && !runId) return null;

  return (
    <div>
      <div className="text-[11px] text-muted-foreground mb-2 flex items-center gap-1">
        <Network className="size-3" /> Crawl coverage
        {tree.length > 0 && (
          <span className="ml-auto font-mono">
            {tree.length} page{tree.length === 1 ? "" : "s"} reachable
            {orphans.length > 0 ? ` · ${orphans.length} unreachable from entrance` : ""}
          </span>
        )}
      </div>
      <div className="rounded-md border border-border bg-surface/60 overflow-x-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-28 gap-2 text-xs text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Loading crawl graph…
          </div>
        ) : error || tree.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-28 gap-1 text-xs text-muted-foreground px-4 text-center">
            No crawl graph yet.
            <span className="text-[10px]">Run "Analyze product" to discover pages.</span>
          </div>
        ) : (
          <svg width={width} height={height} className="block">
            <g opacity={0.4}>
              {tree
                .filter((n) => n.parentId)
                .map((n) => {
                  const parent = tree.find((p) => p.id === n.parentId);
                  if (!parent) return null;
                  const midY = (parent.y + n.y) / 2;
                  return (
                    <path
                      key={n.id}
                      d={`M ${parent.x} ${parent.y} C ${parent.x} ${midY}, ${n.x} ${midY}, ${n.x} ${n.y}`}
                      fill="none"
                      stroke="#6b7280"
                      strokeWidth={1}
                    />
                  );
                })}
            </g>
            {tree.map((n) => {
              const r = n.isRoot ? 11 : 6;
              const color = n.isRoot ? "#f59e0b" : STATUS_COLOR[n.status];
              return (
                <g key={n.id} transform={`translate(${n.x},${n.y})`}>
                  <circle
                    r={r}
                    fill={color}
                    stroke={n.isRoot ? "#fff" : "none"}
                    strokeWidth={n.isRoot ? 2 : 0}
                  />
                  <text
                    y={r + 11}
                    textAnchor="middle"
                    fontSize={n.isRoot ? 10 : 9}
                    fontWeight={n.isRoot ? 600 : 400}
                    fill={n.isRoot ? "#e5e7eb" : "#9ca3af"}
                    fontFamily="monospace"
                  >
                    {n.label}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}
