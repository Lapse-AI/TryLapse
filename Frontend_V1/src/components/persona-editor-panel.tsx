import { useEffect, useState } from "react";
import { Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { usePersonaLibrary } from "@/lib/api/hooks";
import { BookMarked, Users, Trash2, Plus, ChevronDown, ChevronUp, Sparkles, X, Check, Loader2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Avatar helpers (shared palette with persona-studio-panel)
// ---------------------------------------------------------------------------

const AVATAR_PALETTES = [
  { bg: "#4f46e5" }, { bg: "#0891b2" }, { bg: "#059669" },
  { bg: "#d97706" }, { bg: "#7c3aed" }, { bg: "#db2777" },
  { bg: "#0284c7" }, { bg: "#65a30d" },
];

function avatarColor(id: string) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) & 0x7fffffff;
  return AVATAR_PALETTES[h % AVATAR_PALETTES.length].bg;
}

function initials(name: string): string {
  return name.split(/\s+/).slice(0, 2).map((w) => (w[0] ?? "").toUpperCase()).join("");
}

type Persona = {
  id: string; name: string; role: string; goals: string[]; enabled: boolean;
  tech_literacy?: string; patience?: string; trust_level?: string;
  character?: string; usage_context?: string;
};
type Props = { configId: string; live: boolean; onPersonasChanged?: (personas: Persona[]) => void; refreshKey?: number };

// ---------------------------------------------------------------------------
// Edit drawer for a single persona
// ---------------------------------------------------------------------------

function PersonaEditDrawer({
  persona,
  onSave,
  onClose,
  onDelete,
}: {
  persona: Persona;
  onSave: (updated: Persona) => void;
  onClose: () => void;
  onDelete: (id: string) => void;
}) {
  const [name, setName] = useState(persona.name);
  const [role, setRole] = useState(persona.role);
  const [goals, setGoals] = useState(persona.goals.join("\n"));
  const [enabled, setEnabled] = useState(persona.enabled);
  const [techLiteracy, setTechLiteracy] = useState(persona.tech_literacy ?? "intermediate");
  const [patience, setPatience] = useState(persona.patience ?? "medium");
  const [trustLevel, setTrustLevel] = useState(persona.trust_level ?? "neutral");
  const [character, setCharacter] = useState(persona.character ?? "");
  const [usageContext, setUsageContext] = useState(persona.usage_context ?? "");

  return (
    <div className="mt-3 ml-0 rounded-2xl border border-border bg-surface-2/50 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground font-mono">{persona.id}</span>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="size-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-[11px] text-muted-foreground">Name</label>
          <input
            className="mt-0.5 w-full text-sm bg-surface border border-border rounded-xl px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            value={name} onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label className="text-[11px] text-muted-foreground">Role</label>
          <input
            className="mt-0.5 w-full text-sm bg-surface border border-border rounded-xl px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            value={role} onChange={(e) => setRole(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="text-[11px] text-muted-foreground">Goals (one per line)</label>
        <textarea
          className="mt-0.5 w-full min-h-[72px] text-sm bg-surface border border-border rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-primary/30"
          value={goals} onChange={(e) => setGoals(e.target.value)}
        />
      </div>

      <div className="border-t border-border/50 pt-3">
        <div className="text-[11px] font-medium text-muted-foreground mb-2">Behavioral profile <span className="font-normal opacity-60">(shapes journey generation)</span></div>
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[10px] text-muted-foreground">Tech literacy</label>
            <select className="mt-0.5 w-full text-xs bg-surface border border-border rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={techLiteracy} onChange={(e) => setTechLiteracy(e.target.value)}>
              <option value="novice">Novice</option>
              <option value="intermediate">Intermediate</option>
              <option value="expert">Expert</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground">Patience</label>
            <select className="mt-0.5 w-full text-xs bg-surface border border-border rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={patience} onChange={(e) => setPatience(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground">Trust level</label>
            <select className="mt-0.5 w-full text-xs bg-surface border border-border rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={trustLevel} onChange={(e) => setTrustLevel(e.target.value)}>
              <option value="skeptical">Skeptical</option>
              <option value="neutral">Neutral</option>
              <option value="trusting">Trusting</option>
            </select>
          </div>
        </div>
        <div className="mt-2">
          <label className="text-[10px] text-muted-foreground">Character <span className="opacity-60">e.g. "anxious about billing, reads every tooltip"</span></label>
          <input className="mt-0.5 w-full text-xs bg-surface border border-border rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            value={character} onChange={(e) => setCharacter(e.target.value)} placeholder="free-text psychological texture" />
        </div>
        <div className="mt-2">
          <label className="text-[10px] text-muted-foreground">Usage context <span className="opacity-60">e.g. "first-time user", "switching from Competitor X"</span></label>
          <input className="mt-0.5 w-full text-xs bg-surface border border-border rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            value={usageContext} onChange={(e) => setUsageContext(e.target.value)} placeholder="context this persona brings" />
        </div>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <label className="flex items-center gap-2 text-xs cursor-pointer">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} className="accent-primary" />
          <span className="text-muted-foreground">Enabled in runs</span>
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onDelete(persona.id)}
            className="text-xs px-3 py-1.5 rounded-full border border-danger/30 text-danger hover:bg-danger/5 flex items-center gap-1"
          >
            <Trash2 className="size-3" /> Remove
          </button>
          <button
            type="button"
            onClick={() => onSave({ ...persona, name, role, goals: goals.split("\n").map(g => g.trim()).filter(Boolean), enabled, tech_literacy: techLiteracy, patience, trust_level: trustLevel, character: character || undefined, usage_context: usageContext || undefined })}
            className="text-xs px-4 py-1.5 rounded-full bg-primary text-primary-foreground flex items-center gap-1 font-medium"
          >
            <Check className="size-3" /> Save
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Add persona drawer
// ---------------------------------------------------------------------------

function AddPersonaDrawer({
  live,
  onAdd,
  onClose,
}: {
  live: boolean;
  onAdd: (p: Persona) => void;
  onClose: () => void;
}) {
  const [draftPrompt, setDraftPrompt] = useState("");
  const [draftPending, setDraftPending] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [goals, setGoals] = useState("");

  const draftWithAI = async () => {
    if (!live || !draftPrompt.trim()) return;
    setDraftPending(true);
    try {
      const out = await api.draftPersona({ prompt: draftPrompt.trim() });
      const p = out.persona as Persona;
      onAdd({ ...p, enabled: true });
      toast.success(out.source === "llm" ? "Persona drafted with AI" : "Persona drafted (template)");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setDraftPending(false);
    }
  };

  const addManual = () => {
    if (!name.trim()) return;
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 20);
    const id = `p-${slug}-${Date.now().toString(36)}`;
    onAdd({ id, name, role, goals: goals.split("\n").map(g => g.trim()).filter(Boolean), enabled: true });
  };

  return (
    <div className="col-span-full rounded-2xl border border-border bg-surface p-4 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium flex items-center gap-2">
          <Sparkles className="size-4 text-primary" /> Add a persona
        </span>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="size-4" />
        </button>
      </div>

      {/* AI draft */}
      <div className="space-y-2">
        <label className="text-[11px] text-muted-foreground">Describe a user type — AI drafts the persona</label>
        <div className="flex gap-2">
          <input
            className="flex-1 text-sm bg-surface-2 border border-border rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30"
            placeholder='e.g. "HR manager who reviews audit logs and manages access"'
            value={draftPrompt}
            onChange={(e) => setDraftPrompt(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") void draftWithAI(); }}
          />
          <button
            type="button"
            disabled={!live || draftPending || !draftPrompt.trim()}
            onClick={() => void draftWithAI()}
            className="flex items-center gap-1.5 text-xs px-4 py-2 rounded-full bg-primary text-primary-foreground disabled:opacity-40 font-medium shrink-0"
          >
            {draftPending ? <Loader2 className="size-3 animate-spin" /> : <Sparkles className="size-3" />}
            {draftPending ? "Drafting…" : "Draft"}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
        <div className="flex-1 h-px bg-border" />
        or fill manually
        <div className="flex-1 h-px bg-border" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <input
          className="text-sm bg-surface-2 border border-border rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30"
          placeholder="Name"
          value={name} onChange={(e) => setName(e.target.value)}
        />
        <input
          className="text-sm bg-surface-2 border border-border rounded-xl px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30"
          placeholder="Role"
          value={role} onChange={(e) => setRole(e.target.value)}
        />
      </div>
      <textarea
        className="w-full min-h-[56px] text-sm bg-surface-2 border border-border rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-primary/30"
        placeholder="Goals (one per line)"
        value={goals} onChange={(e) => setGoals(e.target.value)}
      />
      <button
        type="button"
        disabled={!name.trim()}
        onClick={addManual}
        className="text-xs px-4 py-1.5 rounded-full bg-primary text-primary-foreground disabled:opacity-40 font-medium"
      >
        Add persona
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

export function PersonaEditorPanel({ configId, live, onPersonasChanged, refreshKey }: Props) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaLens, setPersonaLens] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showLibraryPicker, setShowLibraryPicker] = useState(false);
  const { data: libraryPersonas = [] } = usePersonaLibrary();

  const load = async () => {
    if (!live || !configId) return;
    setLoading(true);
    try {
      const data = await api.getConfigPersonas(configId);
      setPersonas(data.personas);
      setPersonaLens(data.personaLens);
      setDirty(false);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, [configId, live, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const mark = (updater: (prev: Persona[]) => Persona[]) => { setPersonas(updater); setDirty(true); };

  const save = async () => {
    if (!live) { toast.error("Start rehearse serve first"); return; }
    setSaving(true);
    try {
      await api.replaceConfigPersonas({ configId, personas, personaLens });
      toast.success("Personas saved to config");
      setDirty(false);
      onPersonasChanged?.(personas);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    } finally { setSaving(false); }
  };

  const handleAdd = (p: Persona) => {
    setPersonas((prev) => {
      const next = [...prev, p];
      setDirty(true);
      onPersonasChanged?.(next);
      return next;
    });
    setShowAddForm(false);
    setExpanded(p.id);
  };

  const handleSaveEdit = (updated: Persona) => {
    setPersonas((prev) => {
      const next = prev.map((p) => (p.id === updated.id ? updated : p));
      setDirty(true);
      onPersonasChanged?.(next);
      return next;
    });
    setExpanded(null);
  };

  const handleDelete = (id: string) => {
    setPersonas((prev) => {
      const next = prev.filter((p) => p.id !== id);
      setDirty(true);
      onPersonasChanged?.(next);
      return next;
    });
    setExpanded(null);
  };

  if (!live) {
    return (
      <div className="rounded-2xl border border-border p-6 text-sm text-muted-foreground">
        <Users className="size-5 opacity-30 mb-2" />
        Start rehearse serve to manage personas.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-border p-6 flex items-center gap-2 text-sm text-muted-foreground animate-pulse">
        <Loader2 className="size-4 animate-spin" /> Loading personas…
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Actions bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {personas.length > 0 && (
            <span className="text-[11px] text-muted-foreground">{personas.length} persona{personas.length !== 1 ? "s" : ""} in config</span>
          )}
          {dirty && <Chip tone="warn">unsaved changes</Chip>}
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
            <input type="checkbox" checked={personaLens}
              onChange={(e) => { setPersonaLens(e.target.checked); setDirty(true); }}
              className="accent-primary"
            />
            Persona lens
          </label>
          {libraryPersonas.length > 0 && (
            <button
              type="button"
              onClick={() => { setShowLibraryPicker(!showLibraryPicker); setShowAddForm(false); }}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border hover:bg-surface-2 text-muted-foreground"
              title="Add persona from library"
            >
              <BookMarked className="size-3" /> Library
              {showLibraryPicker ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
            </button>
          )}
          {dirty && (
            <button
              type="button"
              disabled={saving}
              onClick={() => void save()}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-primary text-primary-foreground disabled:opacity-40 font-medium"
            >
              {saving ? <Loader2 className="size-3 animate-spin" /> : <Check className="size-3" />}
              {saving ? "Saving…" : "Save"}
            </button>
          )}
        </div>
      </div>

      {/* Library persona picker */}
      {showLibraryPicker && libraryPersonas.length > 0 && (
        <div className="border border-primary/20 rounded-2xl bg-primary/5 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-medium">
              <BookMarked className="size-3.5 text-primary" />
              <span>Add from library</span>
              <span className="text-muted-foreground font-normal">— click to add to this config</span>
            </div>
            <button type="button" onClick={() => setShowLibraryPicker(false)} className="text-muted-foreground hover:text-foreground">
              <X className="size-3.5" />
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {libraryPersonas
              .filter((lp) => !personas.some((p) => p.id === lp.id))
              .map((lp) => (
                <button
                  key={lp.id}
                  type="button"
                  onClick={() => {
                    const newPersona: Persona = {
                      id: lp.id,
                      name: lp.name,
                      role: lp.role,
                      goals: lp.goals,
                      enabled: true,
                      tech_literacy: lp.tech_literacy,
                      patience: lp.patience,
                      trust_level: lp.trust_level,
                      character: lp.character,
                      usage_context: lp.usage_context,
                    };
                    setPersonas((prev) => [...prev, newPersona]);
                    setDirty(true);
                    setShowLibraryPicker(false);
                    toast.success(`"${lp.name}" added — save config to persist`);
                  }}
                  className="text-left p-2.5 rounded-xl border border-border bg-surface hover:border-primary/40 hover:bg-primary/5 transition-colors"
                >
                  <div className="font-medium text-xs truncate">{lp.name}</div>
                  <div className="text-[10px] text-muted-foreground truncate">{lp.role}</div>
                  <div className="text-[10px] text-muted-foreground/60 mt-0.5">{lp.tech_literacy} · {lp.patience}</div>
                </button>
              ))}
          </div>
          {libraryPersonas.filter((lp) => !personas.some((p) => p.id === lp.id)).length === 0 && (
            <div className="text-xs text-muted-foreground text-center py-2">
              All library personas are already in this config.
            </div>
          )}
        </div>
      )}

      {/* Persona card grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
        {personas.map((p) => (
          <div key={p.id} className="space-y-0">
            <button
              type="button"
              onClick={() => setExpanded(expanded === p.id ? null : p.id)}
              className={`w-full group flex flex-col items-center gap-3 p-4 rounded-2xl border transition-all duration-200 cursor-pointer text-left
                ${expanded === p.id
                  ? "border-primary/40 bg-primary/3 shadow-sm"
                  : "border-border bg-surface hover:border-primary/30 hover:shadow-sm"
                }
                ${!p.enabled ? "opacity-50" : ""}
              `}
            >
              <div
                className="size-12 rounded-full flex items-center justify-center text-sm font-semibold text-white shadow-sm shrink-0"
                style={{ background: avatarColor(p.id) }}
              >
                {initials(p.name) || "?"}
              </div>
              <div className="text-center w-full min-w-0">
                <div className="text-sm font-medium truncate" title={p.name}>{p.name || "—"}</div>
                <div className="text-[11px] text-muted-foreground truncate mt-0.5" title={p.role}>{p.role}</div>
                {p.goals.length > 0 && (
                  <div className="text-[10px] text-muted-foreground/60 mt-1">
                    {p.goals.length} goal{p.goals.length !== 1 ? "s" : ""}
                  </div>
                )}
                {!p.enabled && <Chip tone="neutral">disabled</Chip>}
              </div>
              {/* Hover indicator */}
              <div className={`text-[10px] transition-opacity duration-150 ${expanded === p.id ? "text-primary/60 opacity-100" : "text-muted-foreground/30 opacity-0 group-hover:opacity-100"}`}>
                {expanded === p.id ? "▲ editing" : "✎ edit"}
              </div>
            </button>

            {expanded === p.id && (
              <PersonaEditDrawer
                persona={p}
                onSave={handleSaveEdit}
                onClose={() => setExpanded(null)}
                onDelete={handleDelete}
              />
            )}
          </div>
        ))}

        {/* Add card */}
        {!showAddForm && (
          <button
            type="button"
            onClick={() => setShowAddForm(true)}
            className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/3 text-muted-foreground hover:text-primary transition-all duration-200 min-h-[140px]"
          >
            <div className="size-10 rounded-full border-2 border-dashed border-current flex items-center justify-center">
              <Plus className="size-4" />
            </div>
            <span className="text-xs font-medium">Add persona</span>
          </button>
        )}

        {/* Add form spans full row */}
        {showAddForm && (
          <AddPersonaDrawer live={live} onAdd={handleAdd} onClose={() => setShowAddForm(false)} />
        )}
      </div>
    </div>
  );
}
