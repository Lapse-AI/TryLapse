/**
 * Persona Library page — /$workspaceSlug/personas
 *
 * A workspace-global library of reusable behavioral personas.
 * Users can:
 *   - Browse and filter saved personas by tag / source / search
 *   - AI-generate a rich behavioral persona from a natural-language prompt
 *   - Manually create or edit any persona (all five behavioral-depth fields)
 *   - Delete personas from the library
 *   - Import all personas from an existing config in one click
 *   - Copy persona YAML to clipboard or push directly to a config
 *
 * Architecture note
 * -----------------
 * Personas are stored in artifacts/personas.json (workspace-global, not
 * per-product).  The backend API is at /api/persona-library.
 * From here, users "push" a persona into a config via the existing
 * /api/configs/append-persona endpoint (same one used by PersonaEditorPanel).
 */

import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  usePersonaLibrary,
  useSavePersonaLibrary,
  useGeneratePersona,
  useDeletePersonaLibrary,
  useImportPersonasFromConfig,
  useConfigs,
} from "@/lib/api/hooks";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import type { LibraryPersona } from "@/lib/mock-data/types";
import {
  Sparkles,
  Plus,
  Trash2,
  Check,
  X,
  Copy,
  Download,
  Search,
  Brain,
  User,
  Tag,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api/client";

export const Route = createFileRoute("/$workspaceSlug/personas")({
  head: () => ({ meta: [{ title: "Persona Library — Launch Rehearsal" }] }),
  component: PersonaLibraryPage,
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function sourceChipTone(source: string): "ready" | "info" | "neutral" | "warn" {
  if (source === "ai-generated") return "info";
  if (source === "imported-from-config") return "warn";
  return "neutral";
}

function sourceLabel(source: string) {
  if (source === "ai-generated") return "AI";
  if (source === "imported-from-config") return "imported";
  return "manual";
}

function techLiteracyLabel(v: string) {
  return { novice: "Novice", intermediate: "Intermediate", expert: "Expert" }[v] ?? v;
}

function patienceLabel(v: string) {
  return { low: "Low patience", medium: "Medium", high: "High patience" }[v] ?? v;
}

function trustLabel(v: string) {
  return { skeptical: "Skeptical", neutral: "Neutral", trusting: "Trusting" }[v] ?? v;
}

function personaToYaml(p: LibraryPersona): string {
  const lines = [
    `- id: ${p.id}`,
    `  name: ${p.name}`,
    `  role: ${p.role}`,
    `  goals:`,
    ...(p.goals ?? []).map((g) => `    - ${g}`),
    `  enabled: ${p.enabled}`,
    `  tech_literacy: ${p.tech_literacy}`,
    `  patience: ${p.patience}`,
    `  trust_level: ${p.trust_level}`,
  ];
  if (p.character) lines.push(`  character: "${p.character.replace(/"/g, '\\"')}"`);
  if (p.usage_context) lines.push(`  usage_context: "${p.usage_context.replace(/"/g, '\\"')}"`);
  return lines.join("\n");
}

// ── Blank persona template ────────────────────────────────────────────────────

function blankPersona(): Partial<LibraryPersona> {
  return {
    name: "",
    role: "",
    goals: [],
    enabled: true,
    tech_literacy: "intermediate",
    patience: "medium",
    trust_level: "neutral",
    character: "",
    usage_context: "",
    tags: [],
  };
}

// ── Persona Editor (inline drawer) ───────────────────────────────────────────

function PersonaEditor({
  initial,
  onSave,
  onCancel,
}: {
  initial: Partial<LibraryPersona>;
  onSave: (p: Partial<LibraryPersona> & { name: string; role: string }) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial.name ?? "");
  const [role, setRole] = useState(initial.role ?? "");
  const [goals, setGoals] = useState((initial.goals ?? []).join("\n"));
  const [techLiteracy, setTechLiteracy] = useState(initial.tech_literacy ?? "intermediate");
  const [patience, setPatience] = useState(initial.patience ?? "medium");
  const [trustLevel, setTrustLevel] = useState(initial.trust_level ?? "neutral");
  const [character, setCharacter] = useState(initial.character ?? "");
  const [usageContext, setUsageContext] = useState(initial.usage_context ?? "");
  const [tags, setTags] = useState((initial.tags ?? []).join(", "));

  const inputCls =
    "mt-0.5 w-full text-sm bg-surface border border-border rounded-xl px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30";
  const selectCls =
    "mt-0.5 w-full text-xs bg-surface border border-border rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30";

  return (
    <div className="mt-3 rounded-2xl border border-primary/20 bg-primary/5 p-4 space-y-3">
      <div className="text-xs font-medium text-primary">
        {initial.id ? "Edit persona" : "New persona"}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-[11px] text-muted-foreground">Name</label>
          <input
            className={inputCls}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Senior HR Manager"
          />
        </div>
        <div>
          <label className="text-[11px] text-muted-foreground">Role</label>
          <input
            className={inputCls}
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g. HR director, enterprise buyer"
          />
        </div>
      </div>

      <div>
        <label className="text-[11px] text-muted-foreground">
          Goals <span className="opacity-60">(one per line)</span>
        </label>
        <textarea
          className="mt-0.5 w-full min-h-[60px] text-sm bg-surface border border-border rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-primary/30"
          value={goals}
          onChange={(e) => setGoals(e.target.value)}
          placeholder="Review pending approvals&#10;Export compliance report"
        />
      </div>

      {/* Behavioral profile */}
      <div className="border-t border-border/50 pt-2">
        <div className="text-[11px] font-medium text-muted-foreground mb-2">
          Behavioral profile{" "}
          <span className="font-normal opacity-60">
            (shapes journey generation + severity grading)
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[10px] text-muted-foreground">Tech literacy</label>
            <select
              className={selectCls}
              value={techLiteracy}
              onChange={(e) => setTechLiteracy(e.target.value)}
            >
              <option value="novice">Novice</option>
              <option value="intermediate">Intermediate</option>
              <option value="expert">Expert</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground">Patience</label>
            <select
              className={selectCls}
              value={patience}
              onChange={(e) => setPatience(e.target.value)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground">Trust level</label>
            <select
              className={selectCls}
              value={trustLevel}
              onChange={(e) => setTrustLevel(e.target.value)}
            >
              <option value="skeptical">Skeptical</option>
              <option value="neutral">Neutral</option>
              <option value="trusting">Trusting</option>
            </select>
          </div>
        </div>
        <div className="mt-2">
          <label className="text-[10px] text-muted-foreground">Character</label>
          <input
            className={`${inputCls} text-xs`}
            value={character}
            onChange={(e) => setCharacter(e.target.value)}
            placeholder='e.g. "anxious about billing, reads every tooltip"'
          />
        </div>
        <div className="mt-2">
          <label className="text-[10px] text-muted-foreground">Usage context</label>
          <input
            className={`${inputCls} text-xs`}
            value={usageContext}
            onChange={(e) => setUsageContext(e.target.value)}
            placeholder='e.g. "switching from Competitor X" or "first-time user"'
          />
        </div>
        <div className="mt-2">
          <label className="text-[10px] text-muted-foreground">
            Tags <span className="opacity-60">(comma-separated)</span>
          </label>
          <input
            className={`${inputCls} text-xs`}
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="enterprise, mobile-first, compliance"
          />
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-surface-2"
        >
          <X className="size-3 inline mr-1" />
          Cancel
        </button>
        <button
          type="button"
          disabled={!name.trim() || !role.trim()}
          onClick={() =>
            onSave({
              ...initial,
              name: name.trim(),
              role: role.trim(),
              goals: goals
                .split("\n")
                .map((g) => g.trim())
                .filter(Boolean),
              tech_literacy: techLiteracy,
              patience,
              trust_level: trustLevel,
              character: character.trim() || undefined,
              usage_context: usageContext.trim() || undefined,
              tags: tags
                .split(",")
                .map((t) => t.trim())
                .filter(Boolean),
            })
          }
          className="text-xs px-4 py-1.5 rounded-full bg-primary text-primary-foreground flex items-center gap-1 font-medium disabled:opacity-40"
        >
          <Check className="size-3" /> Save to library
        </button>
      </div>
    </div>
  );
}

// ── AI Generate Panel ─────────────────────────────────────────────────────────

function AiGeneratePanel({ onGenerated }: { onGenerated: (p: LibraryPersona) => void }) {
  const [prompt, setPrompt] = useState("");
  const [preview, setPreview] = useState<LibraryPersona | null>(null);
  const generate = useGeneratePersona();
  const save = useSavePersonaLibrary();

  async function handleGenerate() {
    const result = await generate.mutateAsync({ prompt, save: false });
    setPreview(result.persona);
  }

  async function handleSave() {
    if (!preview) return;
    const saved = await save.mutateAsync(preview);
    setPreview(null);
    setPrompt("");
    onGenerated(saved);
  }

  return (
    <div className="border border-primary/20 rounded-2xl bg-primary/5 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-primary" />
        <span className="text-sm font-medium">Generate with AI</span>
        <span className="text-[11px] text-muted-foreground">
          Describe the user in plain language
        </span>
      </div>

      <div className="flex gap-2">
        <textarea
          className="flex-1 min-h-[56px] text-sm bg-surface border border-border rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-primary/30"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder='e.g. "A senior compliance officer at a healthcare company who is skeptical of new software and reads everything carefully"'
        />
        <button
          type="button"
          disabled={!prompt.trim() || generate.isPending}
          onClick={handleGenerate}
          className="self-start px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-medium flex items-center gap-1.5 disabled:opacity-40 whitespace-nowrap"
        >
          <Sparkles className="size-3.5" />
          {generate.isPending ? "Generating…" : "Generate"}
        </button>
      </div>

      {preview && (
        <div className="border border-border rounded-xl p-3 bg-surface space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-medium text-sm">{preview.name}</div>
              <div className="text-xs text-muted-foreground">{preview.role}</div>
            </div>
            <Chip tone="info">AI draft</Chip>
          </div>
          <div className="text-xs text-muted-foreground space-y-0.5">
            {(preview.goals ?? []).map((g, i) => (
              <div key={i}>· {g}</div>
            ))}
          </div>
          <div className="flex gap-2 flex-wrap text-[11px] text-muted-foreground">
            <span>{techLiteracyLabel(preview.tech_literacy)}</span>
            <span>·</span>
            <span>{patienceLabel(preview.patience)}</span>
            <span>·</span>
            <span>{trustLabel(preview.trust_level)}</span>
          </div>
          {preview.character && (
            <div className="text-xs italic text-muted-foreground border-t border-border/50 pt-1.5">
              "{preview.character}"
            </div>
          )}
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={handleSave}
              disabled={save.isPending}
              className="text-xs px-3 py-1.5 rounded-full bg-primary text-primary-foreground flex items-center gap-1 font-medium disabled:opacity-40"
            >
              <Check className="size-3" /> Save to library
            </button>
            <button
              type="button"
              onClick={() => {
                void navigator.clipboard.writeText(personaToYaml(preview));
                toast.success("YAML copied to clipboard");
              }}
              className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-surface-2 flex items-center gap-1"
            >
              <Copy className="size-3" /> Copy YAML
            </button>
            <button
              type="button"
              onClick={() => setPreview(null)}
              className="ml-auto text-muted-foreground hover:text-foreground"
            >
              <X className="size-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Persona Card ──────────────────────────────────────────────────────────────

function PersonaCard({
  persona,
  onEdit,
  onDelete,
  onAddToConfig,
}: {
  persona: LibraryPersona;
  onEdit: (p: LibraryPersona) => void;
  onDelete: (id: string) => void;
  onAddToConfig: (p: LibraryPersona) => void;
}) {
  return (
    <div className="border border-border rounded-2xl p-4 bg-surface hover:bg-surface-2 transition-colors group">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{persona.name}</div>
          <div className="text-xs text-muted-foreground truncate">{persona.role}</div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Chip tone={sourceChipTone(persona.source)}>{sourceLabel(persona.source)}</Chip>
        </div>
      </div>

      {/* Goals */}
      {persona.goals?.length > 0 && (
        <ul className="text-xs text-muted-foreground space-y-0.5 mb-3">
          {persona.goals.slice(0, 2).map((g, i) => (
            <li key={i} className="truncate">
              · {g}
            </li>
          ))}
          {persona.goals.length > 2 && (
            <li className="text-[11px] opacity-60">+{persona.goals.length - 2} more</li>
          )}
        </ul>
      )}

      {/* Behavioral chips */}
      <div className="flex flex-wrap gap-1 mb-3">
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 border border-border text-muted-foreground">
          {techLiteracyLabel(persona.tech_literacy)}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 border border-border text-muted-foreground">
          {patienceLabel(persona.patience)}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 border border-border text-muted-foreground">
          {trustLabel(persona.trust_level)}
        </span>
        {(persona.tags ?? []).map((tag) => (
          <span
            key={tag}
            className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 border border-border/50 text-muted-foreground/70"
          >
            #{tag}
          </span>
        ))}
      </div>

      {/* Character / usage context */}
      {persona.character && (
        <div className="text-[11px] italic text-muted-foreground/80 truncate mb-1">
          "{persona.character}"
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1.5 pt-2 border-t border-border/50 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          type="button"
          onClick={() => onAddToConfig(persona)}
          className="text-[11px] px-2.5 py-1 rounded-full border border-primary/30 text-primary hover:bg-primary/5 flex items-center gap-1"
          title="Add to active config"
        >
          <Plus className="size-3" /> Add to config
        </button>
        <button
          type="button"
          onClick={() => {
            void navigator.clipboard.writeText(personaToYaml(persona));
            toast.success("YAML copied");
          }}
          className="text-[11px] px-2.5 py-1 rounded-full border border-border hover:bg-surface-2"
          title="Copy YAML"
        >
          <Copy className="size-3" />
        </button>
        <button
          type="button"
          onClick={() => onEdit(persona)}
          className="text-[11px] px-2.5 py-1 rounded-full border border-border hover:bg-surface-2"
          title="Edit"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => onDelete(persona.id)}
          className="ml-auto text-[11px] px-2.5 py-1 rounded-full border border-danger/30 text-danger hover:bg-danger/5"
          title="Delete from library"
        >
          <Trash2 className="size-3" />
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

function PersonaLibraryPage() {
  const { workspaceSlug } = Route.useParams();
  const { data: personas = [], isLoading } = usePersonaLibrary();
  const { data: configs = [] } = useConfigs();
  const savePersona = useSavePersonaLibrary();
  const deletePersona = useDeletePersonaLibrary();
  const importFromConfig = useImportPersonasFromConfig();

  const [search, setSearch] = useState("");
  const [filterTag, setFilterTag] = useState("");
  const [editingPersona, setEditingPersona] = useState<Partial<LibraryPersona> | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [showAi, setShowAi] = useState(false);
  const [importConfigId, setImportConfigId] = useState("");

  // All unique tags across the library for the filter dropdown
  const allTags = Array.from(new Set(personas.flatMap((p) => p.tags ?? []))).sort();

  const filtered = personas.filter((p) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      p.name.toLowerCase().includes(q) ||
      p.role.toLowerCase().includes(q) ||
      (p.character ?? "").toLowerCase().includes(q) ||
      (p.usage_context ?? "").toLowerCase().includes(q);
    const matchesTag = !filterTag || (p.tags ?? []).includes(filterTag);
    return matchesSearch && matchesTag;
  });

  async function handleAddToConfig(persona: LibraryPersona) {
    // Use the workspace's active config from configs list
    const activeConfig = configs[0];
    if (!activeConfig) {
      toast.error("No config found — save a config first");
      return;
    }
    try {
      await api.appendPersonaToConfig({
        configId: activeConfig.id,
        persona: persona as Record<string, unknown>,
      });
      toast.success(`"${persona.name}" added to ${activeConfig.id}`);
    } catch (e) {
      toast.error("Failed to add persona to config");
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Library"
        title="Persona Library"
        description={`${personas.length} saved persona${personas.length !== 1 ? "s" : ""} · reusable across all configs`}
        actions={
          <>
            <button
              type="button"
              onClick={() => {
                setShowAi(!showAi);
                setShowNew(false);
                setEditingPersona(null);
              }}
              className="text-xs px-3 py-1.5 rounded-md border border-primary/30 text-primary hover:bg-primary/5 inline-flex items-center gap-1.5"
            >
              <Sparkles className="size-3.5" /> AI generate
            </button>
            <button
              type="button"
              onClick={() => {
                setShowNew(true);
                setShowAi(false);
                setEditingPersona(null);
              }}
              className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
            >
              <Plus className="size-3.5" /> New persona
            </button>
          </>
        }
      />

      <div className="p-4 md:p-8 max-w-[1200px] space-y-6">
        {/* AI generate panel */}
        {showAi && <AiGeneratePanel onGenerated={() => setShowAi(false)} />}

        {/* New persona editor */}
        {showNew && (
          <PersonaEditor
            initial={blankPersona()}
            onSave={(p) => {
              savePersona.mutate(p, { onSuccess: () => setShowNew(false) });
            }}
            onCancel={() => setShowNew(false)}
          />
        )}

        {/* Edit existing persona */}
        {editingPersona && (
          <PersonaEditor
            initial={editingPersona}
            onSave={(p) => {
              savePersona.mutate(p, { onSuccess: () => setEditingPersona(null) });
            }}
            onCancel={() => setEditingPersona(null)}
          />
        )}

        {/* Import from config */}
        <Panel className="p-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Download className="size-4 text-muted-foreground" />
              Import from config
            </div>
            <select
              className="text-xs bg-surface border border-border rounded-lg px-2 py-1.5 flex-1 min-w-[240px] max-w-sm focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={importConfigId}
              onChange={(e) => setImportConfigId(e.target.value)}
            >
              <option value="">Select a config…</option>
              {configs.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={!importConfigId || importFromConfig.isPending}
              onClick={() => {
                importFromConfig.mutate(importConfigId, {
                  onSuccess: () => setImportConfigId(""),
                });
              }}
              className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 disabled:opacity-40 inline-flex items-center gap-1.5"
            >
              {importFromConfig.isPending ? "Importing…" : "Import all"}
            </button>
            <span className="text-[11px] text-muted-foreground">
              Adds all personas from the selected config into this library (idempotent — safe to run
              multiple times).
            </span>
          </div>
        </Panel>

        {/* Search + filter bar */}
        {personas.length > 0 && (
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
              <input
                className="w-full text-sm bg-surface border border-border rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                placeholder="Search personas…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            {allTags.length > 0 && (
              <div className="flex items-center gap-1.5 flex-wrap">
                <Tag className="size-3.5 text-muted-foreground" />
                <button
                  type="button"
                  onClick={() => setFilterTag("")}
                  className={`text-[11px] px-2 py-0.5 rounded-full border ${!filterTag ? "border-primary/40 bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-surface-2"}`}
                >
                  All
                </button>
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => setFilterTag(tag === filterTag ? "" : tag)}
                    className={`text-[11px] px-2 py-0.5 rounded-full border ${filterTag === tag ? "border-primary/40 bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-surface-2"}`}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            )}
            <div className="text-xs text-muted-foreground ml-auto">
              {filtered.length} / {personas.length}
            </div>
          </div>
        )}

        {/* Persona grid */}
        {isLoading ? (
          <div className="text-sm text-muted-foreground p-8 text-center">Loading library…</div>
        ) : filtered.length === 0 && !isLoading ? (
          <div className="border border-dashed border-border rounded-2xl p-12 text-center space-y-3">
            <Brain className="size-8 text-muted-foreground/40 mx-auto" />
            <div className="text-sm font-medium text-muted-foreground">
              {personas.length === 0 ? "Library is empty" : "No matches"}
            </div>
            <div className="text-xs text-muted-foreground max-w-xs mx-auto">
              {personas.length === 0
                ? "Generate a persona with AI, create one manually, or import from a config."
                : "Try a different search or clear the tag filter."}
            </div>
            {personas.length === 0 && (
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAi(true)}
                  className="text-xs px-3 py-1.5 rounded-full bg-primary text-primary-foreground flex items-center gap-1.5"
                >
                  <Sparkles className="size-3.5" /> Generate with AI
                </button>
                <button
                  type="button"
                  onClick={() => setShowNew(true)}
                  className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-surface-2 flex items-center gap-1.5"
                >
                  <Plus className="size-3.5" /> Create manually
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((p) => (
              <PersonaCard
                key={p.id}
                persona={p}
                onEdit={(persona) => {
                  setEditingPersona(persona);
                  setShowNew(false);
                  setShowAi(false);
                }}
                onDelete={(id) => {
                  if (confirm(`Remove "${p.name}" from the library?`)) {
                    deletePersona.mutate(id);
                  }
                }}
                onAddToConfig={handleAddToConfig}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
