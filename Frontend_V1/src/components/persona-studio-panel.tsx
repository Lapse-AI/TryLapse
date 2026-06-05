import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Settings, UserPlus, Sparkles } from "lucide-react";

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
  personaLens: boolean;
  onPersonaLensChange: (value: boolean) => void;
  coreEnabled: Record<string, boolean>;
  onCoreEnabledChange: (id: string, enabled: boolean) => void;
  stagedExtras: PersonaDraft[];
  onStageExtra: (persona: PersonaDraft) => void;
  onRemoveStaged: (id: string) => void;
};

export function PersonaStudioPanel({
  live,
  targetUrl,
  productName,
  configId,
  personaLens,
  onPersonaLensChange,
  coreEnabled,
  onCoreEnabledChange,
  stagedExtras,
  onStageExtra,
  onRemoveStaged,
}: Props) {
  const [prompt, setPrompt] = useState("");
  const [draftFragment, setDraftFragment] = useState("");
  const [lastDraft, setLastDraft] = useState<PersonaDraft | null>(null);
  const [pending, setPending] = useState(false);
  const [corePersonas, setCorePersonas] = useState<PersonaDraft[]>([]);
  const [suggested, setSuggested] = useState<PersonaDraft[]>([]);

  const existingIds = useMemo(
    () => [...corePersonas.map((p) => p.id), ...stagedExtras.map((p) => p.id)],
    [corePersonas, stagedExtras],
  );

  const loadSuggestions = useCallback(async () => {
    if (!live || !targetUrl.trim()) return;
    try {
      const out = await api.suggestPersonas({
        targetUrl: targetUrl.trim(),
        productName: productName.trim() || undefined,
        existingIds,
      });
      setCorePersonas(out.corePersonas);
      setSuggested(out.suggested);
    } catch {
      /* optional */
    }
  }, [live, targetUrl, productName, existingIds]);

  useEffect(() => {
    void loadSuggestions();
  }, [loadSuggestions]);

  const draftPersona = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
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
      toast.success(
        out.source === "llm" ? "Persona drafted with AI" : "Persona drafted (template)",
      );
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
        toast.success(`Added ${persona.name} to ${configId}`);
        void loadSuggestions();
        return;
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Append failed");
        return;
      }
    }
    onStageExtra(persona);
    toast.success(`Staged ${persona.name} — included when you Generate YAML`);
  };

  return (
    <Panel className="p-6 space-y-5 border-dashed border-violet/30">
      <div>
        <div className="flex items-center gap-2 flex-wrap">
          <UserPlus className="size-4 text-violet" />
          <div className="font-display font-semibold">Personas (L2-UI-68)</div>
          <Chip tone="violet">Init step</Chip>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Three core personas are always generated. Describe another user type — AI drafts{" "}
          <span className="font-mono">id / name / role / goals</span> — or pick a product
          suggestion.
        </p>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={personaLens}
          onChange={(e) => onPersonaLensChange(e.target.checked)}
        />
        Use persona lens in scorecard (uncheck for technical-only rehearsal)
      </label>

      <div>
        <div className="text-xs text-muted-foreground mb-2">Core three (always in YAML)</div>
        <div className="space-y-2">
          {(corePersonas.length
            ? corePersonas
            : [
                {
                  id: "p1-evaluator",
                  name: "First-time evaluator",
                  role: "prospect / new user",
                  goals: [],
                  core: true,
                },
                {
                  id: "p2-operator",
                  name: "Daily operator",
                  role: "power user",
                  goals: [],
                  core: true,
                },
                { id: "p3-admin", name: "Admin / buyer", role: "IT admin", goals: [], core: true },
              ]
          ).map((p) => (
            <div
              key={p.id}
              className="flex flex-wrap items-center justify-between gap-2 border border-border rounded-lg px-3 py-2"
            >
              <div>
                <div className="text-sm font-medium">{p.name}</div>
                <div className="text-[11px] text-muted-foreground">{p.role}</div>
              </div>
              <label className="flex items-center gap-1.5 text-xs">
                <input
                  type="checkbox"
                  checked={coreEnabled[p.id] !== false}
                  onChange={(e) => onCoreEnabledChange(p.id, e.target.checked)}
                />
                Include
              </label>
            </div>
          ))}
        </div>
      </div>

      {suggested.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
            <Sparkles className="size-3" /> Suggested for this product
          </div>
          <div className="space-y-2">
            {suggested.map((p) => (
              <div
                key={p.id}
                className="flex flex-wrap items-start justify-between gap-2 border border-border/70 rounded-lg px-3 py-2 bg-surface-2/30"
              >
                <div>
                  <div className="text-sm font-medium">{p.name}</div>
                  <div className="text-[11px] text-muted-foreground">{p.role}</div>
                  {p.reason && (
                    <div className="text-[11px] text-muted-foreground mt-1">{p.reason}</div>
                  )}
                </div>
                <button
                  type="button"
                  className="text-xs px-2 py-1 rounded border border-border hover:bg-surface-2"
                  onClick={() => void addToConfig(p)}
                >
                  Add
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="persona-need" className="text-xs text-muted-foreground">
          Describe a user need
        </label>
        <textarea
          id="persona-need"
          className="w-full min-h-[72px] text-sm bg-surface border border-border rounded-md p-3"
          placeholder='e.g. "SOC2 reviewer who only cares about audit logs and SSO settings"'
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button
          type="button"
          disabled={!live || pending || !prompt.trim()}
          onClick={() => void draftPersona()}
          className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
        >
          {pending ? "Drafting…" : "Draft persona with AI"}
        </button>
      </div>

      {lastDraft && (
        <div className="space-y-2 border border-primary/20 rounded-lg p-3 bg-primary/5">
          <div className="text-sm font-medium">{lastDraft.name}</div>
          <div className="text-[11px] text-muted-foreground font-mono">{lastDraft.id}</div>
          <div className="text-xs">{lastDraft.role}</div>
          <ul className="text-xs list-disc pl-4 text-muted-foreground">
            {lastDraft.goals.map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="text-xs px-3 py-1.5 rounded-md border border-primary/40"
              onClick={() => void addToConfig(lastDraft)}
            >
              {configId ? "Add to config" : "Stage for generate"}
            </button>
            <Link
              to="/config"
              className="text-xs px-3 py-1.5 rounded-md border border-border inline-flex items-center gap-1"
            >
              <Settings className="size-3" /> Config (YAML)
            </Link>
          </div>
          {draftFragment && (
            <pre className="text-[11px] font-mono bg-surface-2 border border-border rounded p-2 overflow-x-auto whitespace-pre-wrap">
              {draftFragment}
            </pre>
          )}
        </div>
      )}

      {stagedExtras.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">Staged extra personas</div>
          <ul className="space-y-1 text-sm">
            {stagedExtras.map((p) => (
              <li key={p.id} className="flex justify-between gap-2 font-mono text-xs">
                <span>
                  {p.id} — {p.name}
                </span>
                <button type="button" className="underline" onClick={() => onRemoveStaged(p.id)}>
                  remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}
