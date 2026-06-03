import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { useConfigs } from "@/lib/api/hooks";
import { toast } from "sonner";
import { Layers } from "lucide-react";

type Props = { live: boolean };

export function CohortRehearsalPanel({ live }: Props) {
  const navigate = useNavigate();
  const { data: configs = [] } = useConfigs();
  const saved = configs.filter((c) => !/\d{8}-\d{6}$/.test(c.id));

  const [configId, setConfigId] = useState("");
  const [nSeeds, setNSeeds] = useState(3);
  const [hypothesis, setHypothesis] = useState("");
  const [useLlm, setUseLlm] = useState(true);
  const [running, setRunning] = useState(false);

  const run = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    if (!configId) {
      toast.error("Select a config");
      return;
    }
    const cfg = configs.find((c) => c.id === configId);
    if (!cfg?.path) {
      toast.error("Config path not found");
      return;
    }
    setRunning(true);
    try {
      const job = await api.triggerCohortJob({
        configPath: cfg.path,
        nSeeds,
        hypothesis: hypothesis.trim() || undefined,
        llm: useLlm,
      });
      toast.success(`Cohort started — ${nSeeds} seeds queued`);
      void navigate({ to: "/cohort/$jobId", params: { jobId: job.id } });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to start cohort");
    } finally {
      setRunning(false);
    }
  };

  return (
    <Panel className="p-5 space-y-4 border-dashed border-primary/30">
      <div className="flex items-center gap-2">
        <Layers className="size-4 text-primary" />
        <div className="font-display font-semibold">Cohort rehearsal</div>
        <Chip tone="violet">L3-PRED-03</Chip>
      </div>
      <p className="text-sm text-muted-foreground">
        Run the same config N times and aggregate readiness into a confidence band. Reveals flaky
        results and confirms repeatability before shipping.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Config</label>
          <select
            aria-label="Config"
            value={configId}
            onChange={(e) => setConfigId(e.target.value)}
            className="w-full text-xs font-mono bg-surface border border-border rounded-md px-2 py-1.5"
          >
            <option value="">— select —</option>
            {saved.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id}.yaml
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Seeds (2–10)</label>
          <input
            type="number"
            min={2}
            max={10}
            value={nSeeds}
            onChange={(e) => setNSeeds(Math.max(2, Math.min(10, Number(e.target.value))))}
            className="w-full text-sm bg-surface border border-border rounded-md px-3 py-1.5"
          />
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Hypothesis (optional)</label>
        <input
          className="w-full text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
          placeholder='e.g. "Core workflow is repeatable across runs"'
          value={hypothesis}
          onChange={(e) => setHypothesis(e.target.value)}
        />
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-1.5 text-xs">
          <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />
          LLM enrichment
        </label>
        <button
          type="button"
          disabled={!live || running || !configId}
          onClick={() => void run()}
          className="flex items-center gap-1.5 text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-40"
        >
          <Layers className="size-3.5" />
          {running ? "Starting…" : `Run ${nSeeds} seeds`}
        </button>
      </div>
    </Panel>
  );
}
