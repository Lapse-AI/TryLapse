import { Panel, Chip } from "@/components/ui-bits";
import type { InsightNarrative } from "@/lib/mock-data/types";
import { Sparkles } from "lucide-react";

export function InsightNarrativePanel({
  title,
  narrative,
}: {
  title: string;
  narrative: InsightNarrative | undefined;
}) {
  if (!narrative) return null;
  const tone =
    narrative.verdict === "improved"
      ? "ready"
      : narrative.verdict === "regressed"
        ? "danger"
        : "warn";

  return (
    <Panel className="p-4 md:p-5 space-y-3 border-primary/20 bg-primary/5">
      <div className="flex items-center gap-2 flex-wrap">
        <Sparkles className="size-4 text-primary" />
        <h2 className="font-display text-lg font-semibold">{title}</h2>
        <Chip tone={tone}>{narrative.verdict}</Chip>
        <Chip tone="neutral">{narrative.source === "llm+template" ? "AI + rules" : "Rules"}</Chip>
      </div>
      <p className="text-sm leading-relaxed">{narrative.headline}</p>
      <div className="grid md:grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs text-muted-foreground mb-1">For founders</div>
          <p className="whitespace-pre-wrap">{narrative.forFounders}</p>
        </div>
        <div>
          <div className="text-xs text-muted-foreground mb-1">For engineering</div>
          <p className="whitespace-pre-wrap">{narrative.forEngineering}</p>
        </div>
      </div>
      {narrative.suggestedQuestions && narrative.suggestedQuestions.length > 0 && (
        <ul className="text-sm space-y-1 list-disc pl-5">
          {narrative.suggestedQuestions.map((q) => (
            <li key={q}>{q}</li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
