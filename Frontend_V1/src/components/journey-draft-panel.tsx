import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Settings } from "lucide-react";

export function JourneyDraftPanel({
  live,
  targetUrl,
}: {
  live: boolean;
  targetUrl: string;
}) {
  const [prompt, setPrompt] = useState("");
  const [fragment, setFragment] = useState("");
  const [pending, setPending] = useState(false);

  const draft = async () => {
    if (!live) {
      toast.error("Start rehearse serve first");
      return;
    }
    if (!targetUrl.trim()) {
      toast.error("Enter a target URL first");
      return;
    }
    setPending(true);
    try {
      const out = await api.draftJourney(prompt, targetUrl.trim());
      setFragment(out.yamlFragment);
      toast.success("Journey draft ready — paste into Config (YAML)");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setPending(false);
    }
  };

  return (
    <Panel className="p-6 space-y-4 border-dashed border-primary/30">
      <div>
        <div className="font-display font-semibold">Describe a journey (prompt → draft)</div>
        <p className="text-sm text-muted-foreground mt-1">
          Plain-language intent becomes a YAML journey fragment. Refine on{" "}
          <Link to="/config" className="text-primary hover:underline">
            Config (YAML)
          </Link>{" "}
          before running.
        </p>
      </div>
      <textarea
        aria-label="Journey description"
        className="w-full min-h-[80px] text-sm bg-surface border border-border rounded-md p-3"
        placeholder='e.g. "Sign up with email, land on dashboard, click Compare runs"'
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button
        type="button"
        disabled={!live || pending || !prompt.trim()}
        onClick={() => void draft()}
        className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
      >
        {pending ? "Drafting…" : "Draft journey YAML"}
      </button>
      {fragment && (
        <div className="space-y-3">
          <pre className="text-[11px] font-mono bg-surface-2 border border-border rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">
            {fragment}
          </pre>
          <Link
            to="/config"
            className="text-xs px-3 py-1.5 rounded-md border border-primary/40 text-primary hover:bg-primary/10 inline-flex items-center gap-1.5"
          >
            <Settings className="size-3.5" /> Paste into Config (YAML)
          </Link>
        </div>
      )}
    </Panel>
  );
}
