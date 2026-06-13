import { useEffect, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { useApiHealth, useConfigYaml, useConfigs } from "@/lib/api/hooks";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { setSelectedConfigId } from "@/lib/selected-config";
import { toast } from "sonner";

type Props = {
  /** When set, pre-selects this config and filters the dropdown to only show
   *  configs whose ID starts with the same prefix (e.g. "argyle" shows
   *  argyle.yaml, argyle-20260610-*.yaml, etc.). */
  workspaceConfigId?: string | null;
};

export function ConfigYamlEditor({ workspaceConfigId }: Props) {
  const { data: live } = useApiHealth();
  const { data: allConfigs = [] } = useConfigs();
  const { configId, pickConfig } = usePersistedConfigId();
  const [busy, setBusy] = useState<"validate" | "save" | null>(null);
  const [valid, setValid] = useState<boolean | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  // Effective config ID: workspace config takes precedence over persisted
  const effectiveConfigId = workspaceConfigId ?? configId;

  // Filter to workspace-relevant configs only
  const prefix = workspaceConfigId?.split("-")[0] ?? "";
  const relevantConfigs = allConfigs.filter((c) => {
    if (c.source !== "saved") return false;
    if (!workspaceConfigId) return true;
    return c.id === workspaceConfigId || (prefix && c.id.startsWith(prefix + "-"));
  });

  // Sort newest first (timestamp in ID — YYYYMMDD-HHmmss sorts lexicographically)
  const sortedConfigs = [...relevantConfigs].sort((a, b) => b.id.localeCompare(a.id));
  const latestId = sortedConfigs[0]?.id ?? workspaceConfigId ?? "";

  // Auto-select the latest version when the workspace config first loads
  const resolvedId =
    effectiveConfigId && relevantConfigs.some((c) => c.id === effectiveConfigId)
      ? effectiveConfigId
      : latestId;

  const { data: file, refetch } = useConfigYaml(resolvedId);
  const [text, setText] = useState("");

  useEffect(() => {
    if (file?.yaml) {
      setText(file.yaml);
      setValid(null);
      setErrors([]);
    }
  }, [file?.yaml]);

  // When workspace config loads, sync persisted ID so Runner also uses it
  useEffect(() => {
    if (workspaceConfigId && workspaceConfigId !== configId) {
      pickConfig(workspaceConfigId);
    }
  }, [workspaceConfigId]); // eslint-disable-line react-hooks/exhaustive-deps

  const validate = async () => {
    if (!live) {
      toast.error("Start ./rehearse serve first");
      return;
    }
    setBusy("validate");
    try {
      const r = await api.validateConfigYaml(text);
      setValid(r.valid);
      setErrors(r.errors ?? []);
      if (r.valid) toast.success("YAML valid");
      else toast.error(r.errors?.[0] ?? "Invalid");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Validate failed");
    } finally {
      setBusy(null);
    }
  };

  const save = async () => {
    if (!live) {
      toast.error("Start ./rehearse serve first");
      return;
    }
    setBusy("save");
    try {
      await api.saveConfigYaml(text, resolvedId);
      setSelectedConfigId(resolvedId);
      toast.success(`Saved ${resolvedId}.yaml`);
      setValid(true);
      void refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Panel className="overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-muted-foreground">
          Config YAML · edit directly or via panels above
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {sortedConfigs.length > 1 ? (
            <div className="flex items-center gap-1.5">
              <select
                aria-label="Config version"
                value={resolvedId}
                onChange={(e) => pickConfig(e.target.value)}
                className="text-xs font-mono bg-surface-2 border border-border rounded-lg px-2 py-1.5 max-w-[200px]"
              >
                {sortedConfigs.map((c, i) => (
                  <option key={c.id} value={c.id}>
                    {c.id}.yaml{i === 0 ? " (latest)" : ""}
                  </option>
                ))}
              </select>
              <span className="text-[10px] text-muted-foreground/60 font-mono">
                {sortedConfigs.length}v
              </span>
            </div>
          ) : (
            <span className="text-xs font-mono text-muted-foreground">
              {resolvedId}.yaml
              {sortedConfigs.length === 1 && (
                <span className="text-muted-foreground/50 ml-1">(latest)</span>
              )}
            </span>
          )}
          <Chip tone={valid === true ? "ready" : valid === false ? "danger" : "neutral"}>
            {valid === true ? "valid" : valid === false ? "invalid" : "unvalidated"}
          </Chip>
          <button
            type="button"
            disabled={!live || busy !== null}
            onClick={() => void validate()}
            className="text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-surface-2 disabled:opacity-50"
          >
            {busy === "validate" ? "…" : "Validate"}
          </button>
          <button
            type="button"
            disabled={!live || busy !== null}
            onClick={() => void save()}
            className="text-xs px-3 py-1.5 rounded-lg bg-primary text-primary-foreground disabled:opacity-50 font-medium"
          >
            {busy === "save" ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
      <textarea
        aria-label="rehearse.yaml editor"
        className="w-full min-h-[380px] p-5 text-[12.5px] font-mono leading-relaxed bg-surface-2/20 text-foreground/95 border-0 focus:outline-none focus:ring-1 focus:ring-primary/20 resize-y"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setValid(null);
        }}
        spellCheck={false}
      />
      {errors.length > 0 && (
        <div className="px-4 py-2 border-t border-border text-xs text-danger font-mono">
          {errors.join(" · ")}
        </div>
      )}
    </Panel>
  );
}
