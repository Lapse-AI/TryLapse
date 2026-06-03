import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { useConfigs } from "@/lib/api/hooks";
import { toast } from "sonner";
import { GitCompare, FlaskConical } from "lucide-react";

type Props = { live: boolean };

export function VariantRehearsalPanel({ live }: Props) {
  const navigate = useNavigate();
  const { data: configs = [] } = useConfigs();
  const saved = configs.filter((c) => c.source === "saved");

  const [configAId, setConfigAId] = useState("");
  const [configBId, setConfigBId] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [userGoal, setUserGoal] = useState("");
  const [useLlm, setUseLlm] = useState(true);
  const [running, setRunning] = useState(false);

  const configPath = (id: string) => configs.find((c) => c.id === id)?.path ?? "";

  const run = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    if (!configAId || !configBId) {
      toast.error("Select both configs");
      return;
    }
    if (configAId === configBId) {
      toast.error("Configs must be different");
      return;
    }
    const pathA = configPath(configAId);
    const pathB = configPath(configBId);
    if (!pathA || !pathB) {
      toast.error("Config path not found");
      return;
    }
    setRunning(true);
    try {
      const job = await api.triggerVariantJob({
        configAPath: pathA,
        configBPath: pathB,
        hypothesis: hypothesis.trim() || undefined,
        userGoal: userGoal.trim() || undefined,
        llm: useLlm,
      });
      toast.success("Variant rehearsal started — running config A first");
      void navigate({ to: "/experiment/$jobId", params: { jobId: job.id } });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to start variant job");
    } finally {
      setRunning(false);
    }
  };

  return (
    <Panel className="p-5 space-y-4 border-dashed border-primary/30">
      <div className="flex items-center gap-2">
        <FlaskConical className="size-4 text-primary" />
        <div className="font-display font-semibold">Variant rehearsal</div>
        <Chip tone="violet">L3-PRED-06</Chip>
      </div>
      <p className="text-sm text-muted-foreground">
        Run two configs (control vs variant) sequentially on the same URL, then get a side-by-side
        experiment report — directional readiness delta before you merge.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Config A — control</label>
          <select
            aria-label="Config A"
            value={configAId}
            onChange={(e) => setConfigAId(e.target.value)}
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
          <label className="text-xs text-muted-foreground">Config B — variant</label>
          <select
            aria-label="Config B"
            value={configBId}
            onChange={(e) => setConfigBId(e.target.value)}
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
      </div>

      <div className="space-y-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Hypothesis (optional)</label>
          <input
            className="w-full text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            placeholder='e.g. "Shorter onboarding improves evaluator journey completion"'
            value={hypothesis}
            onChange={(e) => setHypothesis(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">User goal (optional)</label>
          <input
            className="w-full text-sm bg-surface border border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            placeholder='e.g. "Complete signup without support"'
            value={userGoal}
            onChange={(e) => setUserGoal(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-1.5 text-xs">
          <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />
          LLM enrichment
        </label>
        <button
          type="button"
          disabled={!live || running || !configAId || !configBId}
          onClick={() => void run()}
          className="flex items-center gap-1.5 text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-40"
        >
          <GitCompare className="size-3.5" />
          {running ? "Starting…" : "Run variant rehearsal"}
        </button>
      </div>
    </Panel>
  );
}
