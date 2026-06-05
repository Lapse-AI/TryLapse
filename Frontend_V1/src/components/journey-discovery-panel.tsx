import { useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Map, Loader2, Sparkles, ChevronDown, ChevronUp } from "lucide-react";

type PersonaDraft = { id: string; name: string; role: string; goals: string[] };
type DiscoveredJourney = Record<string, unknown>;
type PersonaJourneys = {
  personaName: string;
  personaRole: string;
  journeys: DiscoveredJourney[];
  usage_pattern?: Record<string, unknown>;
  pain_points_anticipated?: unknown[];
};

type Props = {
  live: boolean;
  personas: PersonaDraft[];
};

function JourneyRow({ j }: { j: DiscoveredJourney }) {
  const [open, setOpen] = useState(false);
  const steps = (j.steps as unknown[]) ?? [];
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-surface-2/30 text-left"
        onClick={() => setOpen(!open)}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium">{String(j.name ?? "")}</span>
            <Chip
              tone={
                j.priority === "critical" ? "danger" : j.priority === "high" ? "warn" : "neutral"
              }
            >
              {String(j.priority ?? "medium")}
            </Chip>
            <Chip tone="neutral">{String(j.frequency ?? "")}</Chip>
            <span className="text-[11px] text-muted-foreground">{steps.length} steps</span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5 truncate">
            {String(j.description ?? "")}
          </div>
        </div>
        {open ? (
          <ChevronUp className="size-4 shrink-0" />
        ) : (
          <ChevronDown className="size-4 shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-3 pb-3 border-t border-border space-y-2 pt-2">
          {steps.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] text-muted-foreground">Steps</div>
              {(steps as Array<Record<string, string>>).map((s, i) => (
                <div key={i} className="text-xs flex gap-2">
                  <Chip tone="neutral">{s.action}</Chip>
                  <span className="text-muted-foreground">
                    {s.description || s.intent || s.url || ""}
                  </span>
                </div>
              ))}
            </div>
          )}
          {j.behavioral_intent && (
            <div>
              <div className="text-[11px] text-muted-foreground">Behavioral intent</div>
              <p className="text-xs">{String(j.behavioral_intent)}</p>
            </div>
          )}
          {Array.isArray(j.failure_signals) && (j.failure_signals as string[]).length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground">Failure signals to watch</div>
              <ul className="text-xs text-muted-foreground list-disc pl-4">
                {(j.failure_signals as string[]).map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {Array.isArray(j.sub_flows) && (j.sub_flows as unknown[]).length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground">Sub-flows (within-page)</div>
              {(j.sub_flows as Array<Record<string, string>>).map((sf, i) => (
                <div key={i} className="text-xs flex gap-2 mt-1">
                  <span className="font-medium">{sf.name}:</span>
                  <span className="text-muted-foreground">{sf.steps_description}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function JourneyDiscoveryPanel({ live, personas }: Props) {
  const [results, setResults] = useState<PersonaJourneys[]>([]);
  const [loading, setLoading] = useState(false);
  const [activePersona, setActivePersona] = useState<string | null>(null);

  const discover = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    if (personas.length === 0) {
      toast.error("Add personas first");
      return;
    }
    setLoading(true);
    setResults([]);
    try {
      const res = await api.discoverJourneys(personas);
      const journeys = (res.personaJourneys ?? []) as PersonaJourneys[];
      setResults(journeys);
      if (journeys.length > 0) setActivePersona(personas[0]?.id ?? null);
      toast.success(
        `Discovered journeys for ${journeys.length} persona${journeys.length === 1 ? "" : "s"}`,
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Discovery failed");
    } finally {
      setLoading(false);
    }
  };

  const discoverOne = async (persona: PersonaDraft) => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    setLoading(true);
    try {
      const res = await api.discoverJourneysForPersona(persona);
      setResults((prev) => {
        const filtered = prev.filter((r) => r.personaName !== persona.name);
        return [...filtered, res as unknown as PersonaJourneys];
      });
      setActivePersona(persona.id);
      toast.success(`Journeys discovered for ${persona.name}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Discovery failed");
    } finally {
      setLoading(false);
    }
  };

  const activeResult =
    results.find((r) => personas.find((p) => p.id === activePersona)?.name === r.personaName) ??
    results[0];

  return (
    <Panel className="overflow-hidden">
      <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Map className="size-4 text-primary" />
          <span className="font-display font-semibold text-sm">Journey discovery</span>
          <Chip tone="violet">AI-generated</Chip>
          {results.length > 0 && (
            <Chip tone="ready">
              {results.reduce((n, r) => n + ((r.journeys as unknown[])?.length ?? 0), 0)} journeys
            </Chip>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={loading || personas.length === 0 || !live}
            onClick={() => void discover()}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-40"
          >
            {loading ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Sparkles className="size-3.5" />
            )}
            {loading ? "Discovering…" : "Discover all personas"}
          </button>
        </div>
      </div>

      {results.length === 0 ? (
        <div className="p-8 text-center text-sm text-muted-foreground space-y-2">
          <Map className="size-8 mx-auto opacity-30" />
          <p>
            Each persona independently discovers its own journeys based on the product model. Can
            include 10–100 journeys per persona, with sub-flows for chatbots, filters, dashboards.
          </p>
          {!live && <p className="text-xs text-warn">Start rehearse serve to enable discovery</p>}
        </div>
      ) : (
        <div className="flex h-full">
          {/* Persona tabs */}
          <div className="w-40 shrink-0 border-r border-border">
            {personas.map((p) => {
              const r = results.find((r) => r.personaName === p.name);
              const count = (r?.journeys as unknown[])?.length ?? 0;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setActivePersona(p.id)}
                  className={[
                    "w-full text-left px-3 py-2.5 border-b border-border text-xs hover:bg-surface-2/30",
                    activePersona === p.id ? "bg-primary/5 font-medium" : "",
                  ].join(" ")}
                >
                  <div className="truncate">{p.name}</div>
                  <div className="text-muted-foreground">{count} journeys</div>
                  {count === 0 && live && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        void discoverOne(p);
                      }}
                      className="text-[10px] text-primary hover:underline mt-0.5"
                    >
                      Discover
                    </button>
                  )}
                </button>
              );
            })}
          </div>

          {/* Journey list */}
          <div className="flex-1 overflow-auto p-4 space-y-2 max-h-[500px]">
            {activeResult?.usage_pattern && (
              <div className="flex gap-3 text-xs text-muted-foreground mb-3 border border-border rounded-lg px-3 py-2">
                <span>
                  Session:{" "}
                  <strong>
                    {String(
                      (activeResult.usage_pattern as Record<string, unknown>).session_frequency ??
                        "",
                    )}
                  </strong>
                </span>
                <span>
                  Avg:{" "}
                  <strong>
                    {String(
                      (activeResult.usage_pattern as Record<string, unknown>)
                        .avg_session_duration_min ?? "",
                    )}{" "}
                    min
                  </strong>
                </span>
              </div>
            )}
            {((activeResult?.journeys as DiscoveredJourney[]) ?? []).map((j, i) => (
              <JourneyRow key={i} j={j} />
            ))}
            {activeResult?.pain_points_anticipated &&
              (activeResult.pain_points_anticipated as unknown[]).length > 0 && (
                <div className="border border-warn/30 rounded-lg p-3 mt-2">
                  <div className="text-[11px] text-muted-foreground mb-1">
                    Anticipated pain points
                  </div>
                  {(activeResult.pain_points_anticipated as Array<Record<string, string>>).map(
                    (pp, i) => (
                      <div key={i} className="text-xs flex gap-2 mt-1">
                        <Chip tone={pp.severity === "critical" ? "danger" : "warn"}>
                          {pp.severity}
                        </Chip>
                        <span>{pp.concern}</span>
                      </div>
                    ),
                  )}
                </div>
              )}
          </div>
        </div>
      )}
    </Panel>
  );
}
