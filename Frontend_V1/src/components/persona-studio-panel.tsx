import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { UserPlus, Sparkles, Plus, X, ChevronDown, ChevronUp, Users } from "lucide-react";

export type PersonaDraft = {
  id: string;
  name: string;
  role: string;
  goals: string[];
  enabled?: boolean;
  core?: boolean;
  reason?: string;
  source?: string;
};

type Props = {
  live: boolean;
  targetUrl: string;
  productName: string;
  configId?: string;
  productModel?: Record<string, unknown> | null;
  personaLens: boolean;
  onPersonaLensChange: (value: boolean) => void;
  personas: PersonaDraft[];
  onAddPersona: (persona: PersonaDraft) => void;
  onRemovePersona: (id: string) => void;
};

// ---------------------------------------------------------------------------
// Avatar helpers
// ---------------------------------------------------------------------------

const AVATAR_PALETTES = [
  { bg: "#4f46e5", text: "#fff" }, // indigo
  { bg: "#0891b2", text: "#fff" }, // cyan
  { bg: "#059669", text: "#fff" }, // emerald
  { bg: "#d97706", text: "#fff" }, // amber
  { bg: "#7c3aed", text: "#fff" }, // violet
  { bg: "#db2777", text: "#fff" }, // pink
  { bg: "#0284c7", text: "#fff" }, // sky
  { bg: "#65a30d", text: "#fff" }, // lime
];

function avatarPalette(id: string) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) & 0x7fffffff;
  return AVATAR_PALETTES[h % AVATAR_PALETTES.length];
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => (w[0] ?? "").toUpperCase())
    .join("");
}

// ---------------------------------------------------------------------------
// PersonaCard
// ---------------------------------------------------------------------------

function PersonaCard({
  persona,
  onRemove,
}: {
  persona: PersonaDraft;
  onRemove: (id: string) => void;
}) {
  const palette = avatarPalette(persona.id);
  return (
    <div className="group relative flex flex-col items-center gap-3 p-4 rounded-2xl border border-border bg-surface hover:border-primary/30 hover:shadow-md transition-all duration-200 cursor-default">
      {/* Remove button */}
      <button
        type="button"
        onClick={() => onRemove(persona.id)}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 size-5 flex items-center justify-center rounded-full bg-surface-2 hover:bg-danger/10 hover:text-danger text-muted-foreground transition-all"
        title="Remove persona"
      >
        <X className="size-3" />
      </button>
      {/* Avatar */}
      <div
        className="size-12 rounded-full flex items-center justify-center text-sm font-semibold shadow-sm shrink-0"
        style={{ background: palette.bg, color: palette.text }}
      >
        {initials(persona.name) || "?"}
      </div>
      {/* Info */}
      <div className="text-center min-w-0 w-full">
        <div className="text-sm font-medium truncate" title={persona.name}>
          {persona.name}
        </div>
        <div className="text-[11px] text-muted-foreground truncate mt-0.5" title={persona.role}>
          {persona.role}
        </div>
        {persona.goals.length > 0 && (
          <div className="text-[10px] text-muted-foreground/60 mt-1">
            {persona.goals.length} goal{persona.goals.length !== 1 ? "s" : ""}
          </div>
        )}
      </div>
    </div>
  );
}

function AddPersonaCard({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/3 text-muted-foreground hover:text-primary transition-all duration-200 min-h-[120px]"
    >
      <div className="size-10 rounded-full border-2 border-dashed border-current flex items-center justify-center">
        <Plus className="size-4" />
      </div>
      <span className="text-xs font-medium">Add persona</span>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

export function PersonaStudioPanel({
  live,
  targetUrl,
  productName,
  configId,
  productModel,
  personaLens,
  onPersonaLensChange,
  personas,
  onAddPersona,
  onRemovePersona,
}: Props) {
  const [prompt, setPrompt] = useState("");
  const [draftFragment, setDraftFragment] = useState("");
  const [lastDraft, setLastDraft] = useState<PersonaDraft | null>(null);
  const [pending, setPending] = useState(false);
  const [suggested, setSuggested] = useState<PersonaDraft[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [addedModelIds, setAddedModelIds] = useState<Set<string>>(new Set());

  const existingIds = useMemo(() => personas.map((p) => p.id), [personas]);

  const modelSuggested = useMemo<PersonaDraft[]>(() => {
    if (!productModel) return [];
    const userTypes = (productModel.user_types_observed as Array<Record<string, string>>) ?? [];
    return userTypes
      .slice(0, 4)
      .map((u, i) => ({
        id: `model-${i}-${(u.type ?? "user").toLowerCase().replace(/\s+/g, "-")}`,
        name: u.type ?? "User",
        role: u.primary_goal ?? u.type ?? "user",
        goals: [u.primary_goal ?? "", u.evidence ?? ""].filter(Boolean),
      }))
      .filter((p) => !addedModelIds.has(p.id) && !personas.some((s) => s.id === p.id));
  }, [productModel, addedModelIds, personas]);

  const loadSuggestions = useCallback(async () => {
    if (!live || !targetUrl.trim()) return;
    try {
      const out = await api.suggestPersonas({
        targetUrl: targetUrl.trim(),
        productName: productName.trim() || undefined,
        existingIds,
      });
      setSuggested(out.suggested);
    } catch { /* optional */ }
  }, [live, targetUrl, productName, existingIds]);

  useEffect(() => { void loadSuggestions(); }, [loadSuggestions]);

  const prevModelRef = useRef<unknown>(null);
  useEffect(() => {
    if (productModel && productModel !== prevModelRef.current) {
      prevModelRef.current = productModel;
      void loadSuggestions();
    }
  }, [productModel, loadSuggestions]);

  const draftPersona = async () => {
    if (!live) { toast.error("Start rehearse serve first"); return; }
    if (!prompt.trim()) return;
    setPending(true);
    try {
      const out = await api.draftPersona({
        prompt: prompt.trim(),
        targetUrl: targetUrl.trim() || undefined,
        productName: productName.trim() || undefined,
      });
      setDraftFragment(out.yamlFragment);
      setLastDraft(out.persona as PersonaDraft);
      toast.success(out.source === "llm" ? "Persona drafted with AI" : "Persona drafted (template)");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setPending(false);
    }
  };

  const addToConfig = async (persona: PersonaDraft) => {
    if (configId && live) {
      try {
        await api.appendPersonaToConfig({ configId, persona });
        setAddedModelIds((prev) => new Set([...prev, persona.id]));
        onAddPersona(persona);
        toast.success(`Added ${persona.name} to config`);
        void loadSuggestions();
        setLastDraft(null);
        setPrompt("");
        return;
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Append failed");
        return;
      }
    }
    onAddPersona(persona);
    setLastDraft(null);
    setPrompt("");
    toast.success(`Added ${persona.name}`);
  };

  const allSuggestions = [
    ...modelSuggested.map((p) => ({ ...p, _source: "product" as const })),
    ...suggested.map((p) => ({ ...p, _source: "ai" as const })),
  ];

  return (
    <div className="space-y-4">
      {/* Persona lens toggle — inline, low-weight */}
      <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer w-fit">
        <input
          type="checkbox"
          checked={personaLens}
          onChange={(e) => onPersonaLensChange(e.target.checked)}
          className="accent-primary"
        />
        Persona lens in scorecard
      </label>

      {/* Persona grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
        {personas.map((p) => (
          <PersonaCard key={p.id} persona={p} onRemove={onRemovePersona} />
        ))}
        <AddPersonaCard onClick={() => setAddOpen(!addOpen)} />
      </div>

      {/* Add persona drawer */}
      {addOpen && (
        <Panel className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UserPlus className="size-4 text-primary" />
              <span className="text-sm font-medium">Add a persona</span>
            </div>
            <button type="button" onClick={() => setAddOpen(false)} className="text-muted-foreground hover:text-foreground">
              <X className="size-4" />
            </button>
          </div>

          {/* Suggestions from product model */}
          {allSuggestions.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2 flex items-center gap-1.5">
                <Sparkles className="size-3 text-primary" />
                <span>Detected in your product</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {allSuggestions.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => void addToConfig(p)}
                    className="flex items-center gap-3 text-left p-3 rounded-xl border border-border hover:border-primary/40 hover:bg-primary/3 transition-all group"
                  >
                    <div
                      className="size-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0"
                      style={{ background: avatarPalette(p.id).bg, color: "#fff" }}
                    >
                      {initials(p.name)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-medium truncate">{p.name}</div>
                      <div className="text-[11px] text-muted-foreground truncate">{p.role}</div>
                    </div>
                    <Plus className="size-3.5 text-muted-foreground group-hover:text-primary shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* AI draft */}
          <div className="space-y-2">
            <label className="text-[11px] text-muted-foreground">
              Or describe a user type
            </label>
            <textarea
              className="w-full min-h-[64px] text-sm bg-surface-2 border border-border rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-primary/30 resize-none"
              placeholder='e.g. "SOC2 reviewer who only cares about audit logs and SSO settings"'
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <button
              type="button"
              disabled={!live || pending || !prompt.trim()}
              onClick={() => void draftPersona()}
              className="flex items-center gap-1.5 text-xs px-4 py-2 rounded-full bg-primary text-primary-foreground disabled:opacity-50 font-medium"
            >
              {pending ? (
                <><span className="size-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />Drafting…</>
              ) : (
                <><Sparkles className="size-3" />Draft with AI</>
              )}
            </button>
          </div>

          {/* AI draft result */}
          {lastDraft && (
            <div className="flex items-start gap-4 p-4 rounded-xl border border-primary/20 bg-primary/3">
              <div
                className="size-10 rounded-full flex items-center justify-center text-sm font-semibold shrink-0 mt-0.5"
                style={{ background: avatarPalette(lastDraft.id).bg, color: "#fff" }}
              >
                {initials(lastDraft.name)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{lastDraft.name}</div>
                <div className="text-[11px] text-muted-foreground">{lastDraft.role}</div>
                {lastDraft.goals.length > 0 && (
                  <ul className="mt-1.5 space-y-0.5">
                    {lastDraft.goals.map((g) => (
                      <li key={g} className="text-[11px] text-muted-foreground flex items-start gap-1">
                        <span className="text-primary mt-0.5">·</span>{g}
                      </li>
                    ))}
                  </ul>
                )}
                {draftFragment && (
                  <details className="mt-2">
                    <summary className="text-[10px] text-muted-foreground cursor-pointer">YAML preview</summary>
                    <pre className="mt-1 text-[10px] font-mono bg-surface-3 rounded-lg p-2 overflow-x-auto whitespace-pre-wrap">
                      {draftFragment}
                    </pre>
                  </details>
                )}
              </div>
              <button
                type="button"
                onClick={() => void addToConfig(lastDraft)}
                className="shrink-0 text-xs px-3 py-1.5 rounded-full bg-primary text-primary-foreground font-medium"
              >
                Add
              </button>
            </div>
          )}
        </Panel>
      )}

      {/* Empty state — only when no config exists (fresh setup) */}
      {personas.length === 0 && !addOpen && !configId && (
        <div className="text-center py-8 text-sm text-muted-foreground">
          <Users className="size-8 mx-auto opacity-20 mb-2" />
          <p>No personas yet.</p>
          <p className="text-xs mt-0.5">Click <strong>Add persona</strong> to create your first one.</p>
        </div>
      )}
    </div>
  );
}
