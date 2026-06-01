import { useState } from "react";
import { Panel } from "@/components/ui-bits";
import type { Annotation } from "@/lib/mock-data/types";
import { useAddAnnotation } from "@/lib/api/hooks";
import { toast } from "sonner";

export function ManualAnnotationPanel({ runId }: { runId: string }) {
  const addAnnotation = useAddAnnotation(runId);
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");

  const submit = () => {
    if (!title.trim()) {
      toast.error("Title required");
      return;
    }
    const ann: Annotation = {
      id: `ann_manual_${Date.now()}`,
      runId,
      targetType: "finding",
      targetId: `manual-${Date.now()}`,
      action: "manual",
      author: "reviewer",
      note: `${title.trim()}${note.trim() ? ` — ${note.trim()}` : ""}`,
      at: new Date().toISOString(),
    };
    addAnnotation.mutate(ann, {
      onSuccess: () => {
        toast.success("Manual finding saved");
        setTitle("");
        setNote("");
      },
      onError: () => toast.error("Could not save"),
    });
  };

  return (
    <Panel className="p-5 space-y-3 border border-border">
      <div className="text-sm font-medium">Add manual finding</div>
      <p className="text-xs text-muted-foreground">
        Partner notes that are not in automated heuristics. Pin on automated issues to flag for
        follow-up; use this panel for net-new observations.
      </p>
      <input
        className="w-full text-sm bg-surface border border-border rounded-md px-3 py-2"
        placeholder="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        className="w-full min-h-[72px] text-sm bg-surface border border-border rounded-md px-3 py-2"
        placeholder="Detail (optional)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <button
        type="button"
        disabled={addAnnotation.isPending}
        onClick={submit}
        className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
      >
        Pin manual finding
      </button>
    </Panel>
  );
}
