import { useEffect, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { useApiHealth, useConfigYaml } from "@/lib/api/hooks";
import { toast } from "sonner";
import { FlaskConical } from "lucide-react";

type Props = {
  configId: string;
  onSaved?: () => void;
};

/** L3-PRED-02 — hypothesis + user goal before rehearsal (Blok-adjacent). */
export function ExperimentSpecPanel({ configId, onSaved }: Props) {
  const { data: live } = useApiHealth();
  const { data: file, refetch } = useConfigYaml(configId);
  const [hypothesis, setHypothesis] = useState("");
  const [userGoal, setUserGoal] = useState("");
  const [variantLabel, setVariantLabel] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const exp = file?.experiment;
    setHypothesis(exp?.hypothesis ?? "");
    setUserGoal(exp?.userGoal ?? "");
    setVariantLabel(exp?.variantLabel ?? "");
  }, [file?.experiment, configId]);

  const save = async () => {
    if (!live) {
      toast.error("Start ./rehearse serve first");
      return;
    }
    setBusy(true);
    try {
      await api.saveConfigExperiment({
        configId,
        hypothesis,
        userGoal,
        variantLabel,
      });
      toast.success("Experiment spec saved on config");
      void refetch();
      onSaved?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel className="p-5 space-y-4 border-primary/20">
      <div className="flex items-center gap-2 flex-wrap">
        <FlaskConical className="size-4 text-primary" />
        <div className="font-display font-semibold text-sm">Experiment spec</div>
        <Chip tone="neutral">optional</Chip>
      </div>
      <p className="text-[11px] text-muted-foreground max-w-2xl">
        How will users behave if you ship this? Capture hypothesis and goal before running —
        surfaced on run detail and compare (not predicted lift until calibration).
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="md:col-span-2">
          <label htmlFor="exp-hypothesis" className="text-xs text-muted-foreground block mb-1">
            Hypothesis
          </label>
          <input
            id="exp-hypothesis"
            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
            placeholder="e.g. Shorter onboarding increases completion for evaluators"
            value={hypothesis}
            onChange={(e) => setHypothesis(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="exp-goal" className="text-xs text-muted-foreground block mb-1">
            User goal
          </label>
          <input
            id="exp-goal"
            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
            placeholder="e.g. Finish signup without support"
            value={userGoal}
            onChange={(e) => setUserGoal(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="exp-variant" className="text-xs text-muted-foreground block mb-1">
            Variant label
          </label>
          <input
            id="exp-variant"
            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm font-mono"
            placeholder="control · variant-b"
            value={variantLabel}
            onChange={(e) => setVariantLabel(e.target.value)}
          />
        </div>
      </div>
      <button
        type="button"
        disabled={!live || busy || !configId}
        onClick={() => void save()}
        className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
      >
        {busy ? "Saving…" : "Save experiment spec"}
      </button>
    </Panel>
  );
}

export function ExperimentRunBanner({
  experiment,
}: {
  experiment?: { hypothesis?: string; userGoal?: string; variantLabel?: string } | null;
}) {
  if (!experiment?.hypothesis && !experiment?.userGoal && !experiment?.variantLabel) {
    return null;
  }
  return (
    <Panel className="p-4 md:p-5 space-y-2 border-primary/15 bg-primary/5">
      <div className="text-xs text-muted-foreground uppercase tracking-wider">Experiment</div>
      {experiment.variantLabel && <Chip tone="violet">{experiment.variantLabel}</Chip>}
      {experiment.hypothesis && (
        <p className="text-sm">
          <span className="text-muted-foreground">Hypothesis: </span>
          {experiment.hypothesis}
        </p>
      )}
      {experiment.userGoal && (
        <p className="text-sm">
          <span className="text-muted-foreground">User goal: </span>
          {experiment.userGoal}
        </p>
      )}
    </Panel>
  );
}
