import { Panel, Chip } from "@/components/ui-bits";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

type Props = {
  readinessA: number;
  readinessB: number;
  bandA?: string;
  bandB?: string;
  newIssues?: number;
  resolvedIssues?: number;
  verdict: "held" | "regressed" | "inconclusive";
  label?: string;
};

const BAND_COLOR: Record<string, string> = {
  Green: "text-ready",
  Amber: "text-warn",
  Red: "text-danger",
};

function ReadinessBar({ value, band }: { value: number; band?: string }) {
  const color = band === "Green" ? "bg-ready" : band === "Red" ? "bg-danger" : "bg-warn";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className={BAND_COLOR[band ?? ""] ?? "text-muted-foreground"}>{band ?? "—"}</span>
        <span className="font-mono font-semibold tabular-nums">{value}</span>
      </div>
      <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export function LiftCard({
  readinessA,
  readinessB,
  bandA,
  bandB,
  newIssues = 0,
  resolvedIssues = 0,
  verdict,
  label = "Directional",
}: Props) {
  const delta = readinessB - readinessA;
  const Icon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  const deltaColor = delta > 0 ? "text-ready" : delta < 0 ? "text-danger" : "text-muted-foreground";
  const verdictTone = verdict === "held" ? "ready" : verdict === "regressed" ? "danger" : "warn";

  return (
    <Panel className="p-5 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Icon className={`size-4 ${deltaColor}`} />
          <span className="font-display font-semibold text-sm">Readiness lift</span>
          <Chip tone="neutral">{label}</Chip>
        </div>
        <div className="flex items-center gap-2">
          <Chip tone={verdictTone}>
            {verdict === "held"
              ? "Hypothesis held"
              : verdict === "regressed"
                ? "Regressed"
                : "Inconclusive"}
          </Chip>
          <span className={`text-2xl font-display font-bold tabular-nums ${deltaColor}`}>
            {delta > 0 ? "+" : ""}
            {delta}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-1.5">
          <div className="text-[11px] text-muted-foreground font-mono">A · control</div>
          <ReadinessBar value={readinessA} band={bandA} />
        </div>
        <div className="space-y-1.5">
          <div className="text-[11px] text-muted-foreground font-mono">B · variant</div>
          <ReadinessBar value={readinessB} band={bandB} />
        </div>
      </div>

      <div className="flex gap-4 text-sm border-t border-border pt-3">
        <div>
          <span className="text-xs text-muted-foreground">New issues </span>
          <span
            className={`font-mono font-semibold ${newIssues > 0 ? "text-danger" : "text-muted-foreground"}`}
          >
            +{newIssues}
          </span>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">Resolved </span>
          <span
            className={`font-mono font-semibold ${resolvedIssues > 0 ? "text-ready" : "text-muted-foreground"}`}
          >
            -{resolvedIssues}
          </span>
        </div>
        <div className="ml-auto text-[11px] text-muted-foreground italic">
          Directional until G6 calibration (Jun 2027)
        </div>
      </div>
    </Panel>
  );
}
