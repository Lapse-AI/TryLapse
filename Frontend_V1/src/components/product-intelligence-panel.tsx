import { useEffect, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Brain, Edit2, Check, X, Loader2, Sparkles, AlertTriangle } from "lucide-react";

type ProductModel = Record<string, unknown>;

type Props = {
  live: boolean;
  targetUrl?: string;
  productName?: string;
  onModelReady?: (model: ProductModel) => void;
};

function SeverityChip({ s }: { s: string }) {
  const tone = s === "critical" ? "danger" : s === "moderate" ? "warn" : "neutral";
  return <Chip tone={tone}>{s}</Chip>;
}

export function ProductIntelligencePanel({ live, targetUrl, productName, onModelReady }: Props) {
  const [model, setModel] = useState<ProductModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  useEffect(() => {
    if (!live) return;
    setLoading(true);
    api
      .getProductModel()
      .then((m) => {
        setModel(m);
        onModelReady?.(m);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [live, onModelReady]);

  const analyze = async () => {
    if (!live || !targetUrl) {
      toast.error("Start rehearse serve and set a target URL first");
      return;
    }
    setAnalyzing(true);
    try {
      const m = await api.analyzeProduct({ targetUrl, productName });
      setModel(m);
      onModelReady?.(m);
      toast.success(
        m.source === "llm"
          ? "Product analyzed with AI"
          : "Product analyzed (template — add LLM key for deep analysis)",
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const saveEdit = async (field: string, value: string) => {
    if (!model) return;
    const updated = { ...model, [field]: value };
    try {
      const m = await api.updateProductModel({ [field]: value });
      setModel({ ...model, ...m });
      toast.success("Saved");
    } catch {
      setModel(updated);
    }
    setEditingField(null);
  };

  const EditableText = ({ field, label }: { field: string; label: string }) => {
    const value = String(model?.[field] ?? "");
    const isEditing = editingField === field;
    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-muted-foreground font-medium">{label}</span>
          {!isEditing && (
            <button
              type="button"
              onClick={() => {
                setEditingField(field);
                setEditValue(value);
              }}
              className="p-1 rounded hover:bg-surface-2 text-muted-foreground"
            >
              <Edit2 className="size-3" />
            </button>
          )}
        </div>
        {isEditing ? (
          <div className="flex gap-1">
            <textarea
              className="flex-1 text-sm bg-surface border border-border rounded-md px-2 py-1 min-h-[60px] focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
            />
            <div className="flex flex-col gap-1">
              <button
                type="button"
                onClick={() => void saveEdit(field, editValue)}
                className="p-1.5 rounded bg-primary text-primary-foreground"
              >
                <Check className="size-3" />
              </button>
              <button
                type="button"
                onClick={() => setEditingField(null)}
                className="p-1.5 rounded border border-border"
              >
                <X className="size-3" />
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm">
            {value || <span className="text-muted-foreground italic">not set</span>}
          </p>
        )}
      </div>
    );
  };

  if (!live)
    return (
      <Panel className="p-5">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Brain className="size-4" /> Product intelligence — start rehearse serve to analyze
        </div>
      </Panel>
    );

  if (loading)
    return (
      <Panel className="p-5 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> Loading product model…
      </Panel>
    );

  return (
    <Panel className="overflow-hidden">
      <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Brain className="size-4 text-violet" />
          <span className="font-display font-semibold text-sm">Product intelligence</span>
          {model && (
            <Chip tone={model.source === "llm" ? "ready" : "neutral"}>
              {String(model.source ?? "")}
            </Chip>
          )}
        </div>
        <button
          type="button"
          disabled={analyzing || !targetUrl}
          onClick={() => void analyze()}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-violet/90 text-white disabled:opacity-40"
        >
          {analyzing ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Sparkles className="size-3.5" />
          )}
          {analyzing ? "Analyzing…" : model ? "Re-analyze" : "Analyze product"}
        </button>
      </div>

      {!model ? (
        <div className="p-8 text-center text-sm text-muted-foreground space-y-2">
          <Brain className="size-8 mx-auto opacity-30" />
          <p>
            Click "Analyze product" — the AI will read your product, understand what it does, and
            generate personas + journeys based on actual behavior.
          </p>
        </div>
      ) : (
        <div className="p-5 space-y-5">
          <EditableText field="purpose" label="Purpose" />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Product type</div>
              <Chip tone="neutral">{String(model.product_type ?? "")}</Chip>
            </div>
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Technical surface</div>
              <div className="flex flex-wrap gap-1">
                {Object.entries((model.technical_surface as Record<string, boolean>) ?? {})
                  .filter(([, v]) => v)
                  .map(([k]) => (
                    <Chip key={k} tone="info">
                      {k.replace("has_", "").replace("_", " ")}
                    </Chip>
                  ))}
              </div>
            </div>
          </div>

          {Array.isArray(model.core_features) && model.core_features.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Core features</div>
              <div className="flex flex-wrap gap-1.5">
                {(model.core_features as string[]).map((f) => (
                  <Chip key={f} tone="neutral">
                    {f}
                  </Chip>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(model.primary_workflows) && model.primary_workflows.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">
                Primary workflows detected
              </div>
              <div className="space-y-2">
                {(model.primary_workflows as Array<Record<string, string>>)
                  .slice(0, 5)
                  .map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start justify-between gap-2 border border-border rounded-lg px-3 py-2"
                    >
                      <div>
                        <div className="text-sm font-medium">{w.name}</div>
                        <div className="text-[11px] text-muted-foreground">{w.description}</div>
                      </div>
                      <Chip tone="neutral">{w.frequency}</Chip>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {Array.isArray(model.quality_concerns) && model.quality_concerns.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2 flex items-center gap-1">
                <AlertTriangle className="size-3" /> Quality concerns observed
              </div>
              <div className="space-y-1.5">
                {(model.quality_concerns as Array<Record<string, string>>).map((c, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <SeverityChip s={c.severity} />
                    <span className="text-muted-foreground">[{c.area}]</span>
                    <span>{c.concern}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(model.user_types_observed) && model.user_types_observed.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">User types observed</div>
              <div className="space-y-1.5">
                {(model.user_types_observed as Array<Record<string, string>>).map((u, i) => (
                  <div key={i} className="border border-border rounded-lg px-3 py-2">
                    <div className="text-sm font-medium">{u.type}</div>
                    <div className="text-[11px] text-muted-foreground">{u.primary_goal}</div>
                    <div className="text-[10px] text-muted-foreground/70 mt-0.5 italic">
                      {u.evidence}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
