import { useEffect, useState, useMemo, type ElementType, type ReactNode } from "react";
import type { Status, Severity } from "@/lib/mock-data";
import { formatRel } from "@/lib/mock-data";

/** Renders relative time only after mount to avoid SSR/CSR hydration mismatch. */
export function ClientTime({ iso, fallback = "" }: { iso: string; fallback?: string }) {
  const [text, setText] = useState(fallback);
  useEffect(() => {
    setText(formatRel(iso));
    const id = setInterval(() => setText(formatRel(iso)), 60_000);
    return () => clearInterval(id);
  }, [iso]);
  return <span suppressHydrationWarning>{text || fallback}</span>;
}

export function StatusDot({ status, className = "" }: { status: Status; className?: string }) {
  const map: Record<Status, string> = {
    ready: "bg-ready",
    warn: "bg-warn",
    danger: "bg-danger",
    neutral: "bg-muted-foreground/50",
  };
  return <span className={`inline-block size-2 rounded-full ${map[status]} ${className}`} />;
}

export function Chip({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Status | "info" | "violet";
}) {
  const tones: Record<string, string> = {
    ready: "text-ready border-ready/25 bg-ready/8",
    warn: "text-warn border-warn/25 bg-warn/8",
    danger: "text-danger border-danger/25 bg-danger/8",
    info: "text-info border-info/25 bg-info/8",
    violet: "text-violet border-violet/25 bg-violet/8",
    neutral: "text-muted-foreground border-border bg-surface-2",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function SeverityChip({ s }: { s: Severity }) {
  const tone: Record<Severity, "danger" | "warn" | "info" | "neutral"> = {
    P0: "danger",
    P1: "warn",
    P2: "info",
    P3: "neutral",
  };
  return <Chip tone={tone[s]}>{s}</Chip>;
}

export function Panel({
  children,
  className = "",
  as: As = "div",
  id,
}: {
  children: ReactNode;
  className?: string;
  as?: ElementType;
  id?: string;
}) {
  return <As className={`panel ${className}`} id={id}>{children}</As>;
}

export function SectionTitle({
  eyebrow,
  title,
  action,
}: {
  eyebrow?: string;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-end justify-between mb-4">
      <div>
        {eyebrow && <div className="text-xs text-muted-foreground mb-1">{eyebrow}</div>}
        <h2 className="font-display text-xl font-semibold">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div
      className="border-b border-border/50 backdrop-blur-sm"
      style={{ background: "color-mix(in oklab, white 78%, transparent)" }}
    >
      <div className="px-4 md:px-8 py-6 flex items-start justify-between gap-6 flex-wrap">
        <div>
          {/* Eyebrow pill */}
          <div className="inline-flex items-center gap-1.5 mb-3 px-2 py-0.5 rounded-full border border-primary/20 bg-primary/5">
            <span className="size-1.5 rounded-full bg-primary" />
            <span className="text-[11px] text-primary/80 font-semibold uppercase tracking-wider">
              {eyebrow}
            </span>
          </div>
          <h1 className="font-display text-[34px] font-bold tracking-[-0.025em] leading-tight">
            {title}
          </h1>
          {description && (
            <p className="text-muted-foreground mt-2 max-w-prose text-sm leading-relaxed">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
      </div>
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
  tone,
  title,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: Status;
  title?: string;
}) {
  return (
    <div className="panel-glass p-4" title={title}>
      <div className="text-[11px] text-muted-foreground font-medium">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-2">
        <div className="font-display text-2xl font-bold tracking-tight tabular-nums">{value}</div>
        {tone && <StatusDot status={tone} />}
      </div>
      {hint && <div className="text-[11px] text-muted-foreground mt-1">{hint}</div>}
    </div>
  );
}

export function Sparkline({
  values,
  color = "var(--ready)",
  height = 36,
  className = "w-full",
}: {
  values: number[];
  color?: string;
  height?: number;
  className?: string;
}) {
  const { safe, w, coords, points } = useMemo(() => {
    const safe = values.filter((v) => Number.isFinite(v));
    const w = Math.max(120, safe.length * 8);
    if (safe.length === 0) return { safe, w, coords: [] as { x: number; y: number }[], points: "" };
    const min = Math.min(...safe);
    const max = Math.max(...safe);
    const range = max - min || 1;
    const denom = Math.max(safe.length - 1, 1);
    const coords = safe.map((v, i) => ({
      x: (i / denom) * w,
      y: height - ((v - min) / range) * height,
    }));
    return { safe, w, coords, points: coords.map(({ x, y }) => `${x},${y}`).join(" ") };
  }, [values, height]);

  if (safe.length === 0) {
    return <svg viewBox={`0 0 ${w} ${height}`} className={className} aria-hidden />;
  }

  return (
    <svg
      viewBox={`0 0 ${w} ${height}`}
      className={`${className} overflow-visible`}
      preserveAspectRatio="none"
    >
      <polyline fill="none" stroke={color} strokeWidth={1.5} points={points} />
      {coords.map(({ x, y }, i) => (
        <circle key={i} cx={x} cy={y} r={1.5} fill={color} />
      ))}
    </svg>
  );
}

export function ReadinessGauge({ value, band }: { value: number; band?: Status }) {
  // Band is derived from issue severity (passed in). Fallback to score thresholds.
  const tone: Status = band ?? (value >= 80 ? "ready" : value >= 70 ? "warn" : "danger");
  const color = `var(--${tone})`;
  const radius = 78;
  const circumference = 2 * Math.PI * radius;
  const dash = (value / 100) * circumference;
  const bandLabel = tone === "ready" ? "Green" : tone === "warn" ? "Amber" : "Red";

  const glowClass = tone === "ready" ? "glow-ready" : tone === "warn" ? "glow-warn" : "glow-danger";

  return (
    <div
      className={`relative size-[200px] flex items-center justify-center rounded-full ${glowClass}`}
      title={`Score ${value}/100 · Band ${bandLabel} (derived from blocker severity, not the score)`}
    >
      <svg viewBox="0 0 200 200" className="-rotate-90 absolute inset-0">
        {/* Outer glow ring */}
        <circle
          cx="100"
          cy="100"
          r={radius + 8}
          stroke={color}
          strokeWidth="1"
          fill="none"
          opacity="0.12"
        />
        {/* Track */}
        <circle cx="100" cy="100" r={radius} stroke="var(--border)" strokeWidth="7" fill="none" />
        {/* Progress arc */}
        <circle
          cx="100"
          cy="100"
          r={radius}
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${dash} ${circumference}`}
          style={{
            transition: "stroke-dasharray 700ms cubic-bezier(.4,0,.2,1)",
            filter: `drop-shadow(0 0 5px color-mix(in oklab, ${color} 60%, transparent))`,
          }}
        />
      </svg>
      <div className="text-center z-10">
        <div
          className="font-display text-5xl font-bold tabular-nums tracking-tight"
          style={{ color }}
        >
          {value}
        </div>
        <div className="text-[11px] text-muted-foreground mt-1 font-mono">/ 100</div>
        <div className="mt-2">
          <Chip tone={tone}>{bandLabel}</Chip>
        </div>
      </div>
    </div>
  );
}

export function Bar({
  value,
  max = 100,
  tone = "ready",
}: {
  value: number;
  max?: number;
  tone?: "ready" | "warn" | "danger" | "info" | "violet";
}) {
  return (
    <div className="h-1.5 w-full rounded-full bg-surface-3 overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{
          width: `${(value / max) * 100}%`,
          background: `var(--${tone})`,
          boxShadow: `0 0 6px 0 color-mix(in oklab, var(--${tone}) 50%, transparent)`,
        }}
      />
    </div>
  );
}
