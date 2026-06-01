import { artifactUrl } from "@/lib/api/client";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export type FocusRegion = {
  x: number;
  y: number;
  width: number;
  height: number;
  viewportWidth: number;
  viewportHeight: number;
  label?: string;
};

type AnnotatedScreenshotProps = {
  src: string;
  region?: FocusRegion | null;
  alt: string;
  className?: string;
  emptyLabel?: string;
};

export function AnnotatedScreenshot({
  src,
  region,
  alt,
  className = "",
  emptyLabel = "No screenshot",
}: AnnotatedScreenshotProps) {
  if (!src) {
    return (
      <div
        className={`aspect-video flex items-center justify-center text-xs text-muted-foreground bg-surface-2 border border-dashed border-border rounded-md ${className}`}
      >
        {emptyLabel}
      </div>
    );
  }

  const url = src.startsWith("http") ? src : artifactUrl(src);
  const vpW = region?.viewportWidth || 1280;
  const vpH = region?.viewportHeight || 900;
  const showBox = region && region.width > 0 && region.height > 0 && vpW > 0 && vpH > 0;

  return (
    <div
      className={`relative overflow-hidden rounded-md border border-border bg-black/5 ${className}`}
    >
      <img src={url} alt={alt} className="w-full h-auto block" loading="lazy" />
      {showBox && region && (
        <>
          <div
            className="absolute border-2 border-primary pointer-events-none rounded-sm shadow-[0_0_0_1px_rgba(255,255,255,0.6)]"
            style={{
              left: `${(region.x / vpW) * 100}%`,
              top: `${(region.y / vpH) * 100}%`,
              width: `${(region.width / vpW) * 100}%`,
              height: `${(region.height / vpH) * 100}%`,
            }}
            aria-hidden
          />
          {region.label && (
            <div
              className="absolute text-[10px] font-medium px-1.5 py-0.5 rounded bg-primary text-primary-foreground shadow-sm max-w-[90%] truncate pointer-events-none"
              style={{
                left: `${(region.x / vpW) * 100}%`,
                top: `max(0%, calc(${(region.y / vpH) * 100}% - 22px))`,
              }}
            >
              {region.label}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export type VisualStepDiff = {
  stepId: string;
  journeyId?: string;
  action?: string;
  outcomeA?: string | null;
  outcomeB?: string | null;
  screenshotPathA?: string | null;
  screenshotPathB?: string | null;
  focusRegionA?: FocusRegion | null;
  focusRegionB?: FocusRegion | null;
  onlyInB?: boolean;
};

export function CompareVisualDiffPanel({ items }: { items: VisualStepDiff[] }) {
  const withShots = items.filter((i) => i.screenshotPathA || i.screenshotPathB);
  if (!withShots.length) {
    return (
      <PanelPlaceholder message="No visual step diff for this pair. Common causes: same outcomes on every step (try enterprise runs), navigate-only configs (add click/fill steps), or runs from different YAML files." />
    );
  }

  return (
    <Accordion type="single" collapsible className="border border-border rounded-lg divide-y divide-border">
      {withShots.map((item) => {
        const outcomeLabel = item.onlyInB
          ? "new step"
          : `${item.outcomeA ?? "—"} → ${item.outcomeB ?? "—"}`;
        return (
          <AccordionItem key={item.stepId} value={item.stepId} className="border-0">
            <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-surface-2/40 [&[data-state=open]]:bg-surface-2/40">
              <div className="flex flex-wrap items-center gap-2 text-sm text-left flex-1 min-w-0">
                <span className="font-mono text-xs">{item.stepId}</span>
                {item.journeyId && (
                  <span className="text-muted-foreground text-xs">{item.journeyId}</span>
                )}
                {item.action && (
                  <span className="text-muted-foreground text-xs">· {item.action}</span>
                )}
                <span className="text-xs font-mono ml-auto shrink-0">{outcomeLabel}</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pb-0">
              <div className="grid md:grid-cols-2 gap-0 md:divide-x divide-border border-t border-border">
                <div className="p-3 space-y-2">
                  <div className="text-[11px] text-muted-foreground uppercase tracking-wide">
                    Run A
                  </div>
                  <AnnotatedScreenshot
                    src={item.screenshotPathA ?? ""}
                    region={item.focusRegionA}
                    alt={`${item.stepId} run A`}
                    emptyLabel="—"
                  />
                </div>
                <div className="p-3 space-y-2">
                  <div className="text-[11px] text-muted-foreground uppercase tracking-wide">
                    Run B
                  </div>
                  <AnnotatedScreenshot
                    src={item.screenshotPathB ?? ""}
                    region={item.focusRegionB}
                    alt={`${item.stepId} run B`}
                    emptyLabel="—"
                  />
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        );
      })}
    </Accordion>
  );
}

function PanelPlaceholder({ message }: { message: string }) {
  return <p className="text-sm text-muted-foreground text-center py-6 px-4">{message}</p>;
}
