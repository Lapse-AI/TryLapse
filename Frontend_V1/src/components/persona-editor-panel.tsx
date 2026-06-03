import { useEffect, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Users, Trash2, Plus, ChevronDown, ChevronUp, Sparkles } from "lucide-react";

type Persona = {
  id: string;
  name: string;
  role: string;
  goals: string[];
  enabled: boolean;
};

type Props = {
  configId: string;
  live: boolean;
};

export function PersonaEditorPanel({ configId, live }: Props) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaLens, setPersonaLens] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  // AI draft
  const [draftPrompt, setDraftPrompt] = useState("");
  const [draftPending, setDraftPending] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  // manual add form
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState("");
  const [newGoals, setNewGoals] = useState("");

  const load = async () => {
    if (!live || !configId) return;
    setLoading(true);
    try {
      const data = await api.getConfigPersonas(configId);
      setPersonas(data.personas);
      setPersonaLens(data.personaLens);
      setDirty(false);
    } catch {
      // silent — user sees save failure separately
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configId, live]);

  const mark = (updater: (prev: Persona[]) => Persona[]) => {
    setPersonas(updater);
    setDirty(true);
  };

  const save = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    setSaving(true);
    try {
      await api.replaceConfigPersonas({ configId, personas, personaLens });
      toast.success("Personas saved");
      setDirty(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const updateField = (id: string, field: keyof Persona, value: unknown) => {
    mark((prev) => prev.map((p) => (p.id === id ? { ...p, [field]: value } : p)));
  };

  const deletePersona = (id: string) => {
    mark((prev) => prev.filter((p) => p.id !== id));
    if (expanded === id) setExpanded(null);
  };

  const addManual = () => {
    const slug =
      newName
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .slice(0, 20) || "custom";
    const id = `p-${slug}-${Date.now().toString(36)}`;
    const goals = newGoals
      .split("\n")
      .map((g) => g.trim())
      .filter(Boolean);
    mark((prev) => [...prev, { id, name: newName, role: newRole, goals, enabled: true }]);
    setNewName("");
    setNewRole("");
    setNewGoals("");
    setShowAddForm(false);
    setExpanded(id);
  };

  const draftWithAI = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    if (!draftPrompt.trim()) return;
    setDraftPending(true);
    try {
      const out = await api.draftPersona({ prompt: draftPrompt.trim() });
      const p = out.persona as Persona;
      mark((prev) => [...prev, { ...p, enabled: true }]);
      setDraftPrompt("");
      setExpanded(p.id);
      setShowAddForm(false);
      toast.success(
        out.source === "llm" ? "Persona drafted with AI" : "Persona drafted (template)",
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setDraftPending(false);
    }
  };

  if (!live) {
    return (
      <Panel className="p-6">
        <div className="flex items-center gap-2 mb-2">
          <Users className="size-4 text-violet" />
          <span className="font-display font-semibold">Personas</span>
        </div>
        <p className="text-sm text-muted-foreground">Start rehearse serve to edit personas.</p>
      </Panel>
    );
  }

  if (loading) {
    return (
      <Panel className="p-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground animate-pulse">
          <Users className="size-4" /> Loading personas…
        </div>
      </Panel>
    );
  }

  return (
    <Panel className="overflow-hidden">
      <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Users className="size-4 text-violet" />
          <span className="font-display font-semibold">Personas</span>
          <Chip tone="neutral">{personas.length}</Chip>
          {dirty && <Chip tone="warn">unsaved</Chip>}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <label className="flex items-center gap-1.5 text-xs">
            <input
              type="checkbox"
              checked={personaLens}
              onChange={(e) => {
                setPersonaLens(e.target.checked);
                setDirty(true);
              }}
            />
            Persona lens in scorecard
          </label>
          <button
            type="button"
            disabled={!dirty || saving}
            onClick={() => void save()}
            className="text-xs px-3 py-1 rounded bg-primary text-primary-foreground disabled:opacity-40"
          >
            {saving ? "Saving…" : "Save personas"}
          </button>
        </div>
      </div>

      <div className="divide-y divide-border">
        {personas.map((p) => (
          <div key={p.id} className="px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                <label className="flex items-center gap-1.5 text-xs shrink-0">
                  <input
                    type="checkbox"
                    checked={p.enabled}
                    onChange={(e) => updateField(p.id, "enabled", e.target.checked)}
                  />
                  On
                </label>
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">
                    {p.name || <span className="text-muted-foreground italic">unnamed</span>}
                  </div>
                  <div className="text-[11px] text-muted-foreground font-mono truncate">{p.id}</div>
                </div>
                {!p.enabled && <Chip tone="neutral">disabled</Chip>}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                  className="p-1 rounded hover:bg-surface-2 text-muted-foreground"
                  aria-label="expand"
                >
                  {expanded === p.id ? (
                    <ChevronUp className="size-4" />
                  ) : (
                    <ChevronDown className="size-4" />
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => deletePersona(p.id)}
                  className="p-1 rounded hover:bg-danger/10 text-danger/60 hover:text-danger"
                  aria-label="delete"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            </div>

            {expanded === p.id && (
              <div className="mt-3 space-y-3 pl-7">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-muted-foreground">Name</label>
                    <input
                      className="w-full text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                      value={p.name}
                      onChange={(e) => updateField(p.id, "name", e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] text-muted-foreground">Role</label>
                    <input
                      className="w-full text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                      value={p.role}
                      onChange={(e) => updateField(p.id, "role", e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] text-muted-foreground">Goals (one per line)</label>
                  <textarea
                    className="w-full min-h-[80px] text-sm bg-surface border border-border rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30"
                    value={p.goals.join("\n")}
                    onChange={(e) =>
                      updateField(
                        p.id,
                        "goals",
                        e.target.value
                          .split("\n")
                          .map((g) => g.trim())
                          .filter(Boolean),
                      )
                    }
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add persona */}
      <div className="p-4 border-t border-border space-y-3">
        {!showAddForm ? (
          <button
            type="button"
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-1.5 text-xs text-primary hover:underline"
          >
            <Plus className="size-3.5" /> Add persona
          </button>
        ) : (
          <div className="space-y-3 border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Add persona</span>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="text-xs text-muted-foreground hover:underline"
              >
                cancel
              </button>
            </div>

            {/* AI draft */}
            <div className="space-y-2">
              <label className="text-[11px] text-muted-foreground flex items-center gap-1">
                <Sparkles className="size-3" /> Describe a user need (AI draft)
              </label>
              <div className="flex gap-2">
                <input
                  className="flex-1 text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                  placeholder='e.g. "Security reviewer who checks audit logs"'
                  value={draftPrompt}
                  onChange={(e) => setDraftPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void draftWithAI();
                  }}
                />
                <button
                  type="button"
                  disabled={!live || draftPending || !draftPrompt.trim()}
                  onClick={() => void draftWithAI()}
                  className="text-xs px-3 py-1.5 rounded bg-violet/90 text-white disabled:opacity-40 shrink-0"
                >
                  {draftPending ? "Drafting…" : "Draft with AI"}
                </button>
              </div>
            </div>

            <div className="text-[11px] text-muted-foreground text-center">
              — or fill manually —
            </div>

            {/* Manual */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                className="text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                placeholder="Name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <input
                className="text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                placeholder="Role"
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
              />
            </div>
            <textarea
              className="w-full min-h-[60px] text-sm bg-surface border border-border rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30"
              placeholder="Goals (one per line)"
              value={newGoals}
              onChange={(e) => setNewGoals(e.target.value)}
            />
            <button
              type="button"
              disabled={!newName.trim()}
              onClick={addManual}
              className="text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground disabled:opacity-40"
            >
              Add
            </button>
          </div>
        )}
      </div>
    </Panel>
  );
}
