import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { useApiHealth, useConfigYaml, useConfigs } from "@/lib/api/hooks";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { setSelectedConfigId } from "@/lib/selected-config";
import { toast } from "sonner";
import { Wand2, PlayCircle } from "lucide-react";

export function ConfigYamlEditor() {
  const { data: live } = useApiHealth();
  const { data: configs = [] } = useConfigs();
  const saved = configs.filter((c) => c.source === "saved");
  const { configId, pickConfig } = usePersistedConfigId();
  const { data: file, refetch } = useConfigYaml(configId);
  const [text, setText] = useState("");
  const [valid, setValid] = useState<boolean | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState<"validate" | "save" | null>(null);

  useEffect(() => {
    if (file?.yaml) {
      setText(file.yaml);
      setValid(null);
      setErrors([]);
    }
  }, [file?.yaml]);

  const onConfigChange = (id: string) => {
    pickConfig(id);
  };

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
      await api.saveConfigYaml(text, configId);
      setSelectedConfigId(configId);
      toast.success(`Saved ${configId}.yaml — open Runner to rehearse`);
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
      <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs text-muted-foreground">rehearse.yaml · live editor</div>
          <div className="text-[11px] text-muted-foreground mt-1">
            5 journeys required · secrets via env only ·{" "}
            <Link
              to="/init"
              className="text-primary hover:underline inline-flex items-center gap-1"
            >
              <Wand2 className="size-3" /> Init wizard
            </Link>{" "}
            for guided setup
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <select
            aria-label="Config file"
            value={configId}
            onChange={(e) => onConfigChange(e.target.value)}
            className="text-xs font-mono bg-surface border border-border rounded-md px-2 py-1"
          >
            {saved.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id}.yaml
              </option>
            ))}
          </select>
          <Chip tone={valid === true ? "ready" : valid === false ? "danger" : "neutral"}>
            {valid === true ? "valid" : valid === false ? "invalid" : "unvalidated"}
          </Chip>
          <button
            type="button"
            disabled={!live || busy !== null}
            onClick={() => void validate()}
            className="text-xs font-mono px-3 py-1 rounded border border-border hover:bg-surface-2 disabled:opacity-50"
          >
            {busy === "validate" ? "…" : "Validate"}
          </button>
          <button
            type="button"
            disabled={!live || busy !== null}
            onClick={() => void save()}
            className="text-xs font-mono px-3 py-1 rounded bg-primary text-primary-foreground disabled:opacity-50"
          >
            {busy === "save" ? "Saving…" : "Save"}
          </button>
          <Link
            to="/runner"
            className="text-xs font-mono px-3 py-1 rounded border border-primary/40 text-primary hover:bg-primary/10 inline-flex items-center gap-1"
          >
            <PlayCircle className="size-3" /> Run in Runner
          </Link>
        </div>
      </div>
      <textarea
        aria-label="rehearse.yaml editor"
        className="w-full min-h-[420px] p-5 text-[12.5px] font-mono leading-relaxed bg-surface-2/30 text-foreground/95 border-0 focus:outline-none focus:ring-1 focus:ring-primary/30"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setValid(null);
        }}
        spellCheck={false}
      />
      {errors.length > 0 && (
        <div className="px-4 py-3 border-t border-border text-xs text-danger font-mono">
          {errors.join(" · ")}
        </div>
      )}
    </Panel>
  );
}
