import { useEffect, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { useApiHealth } from "@/lib/api/hooks";
import { getMockChatThread, mockChatReply } from "@/lib/mock-data/store";
import { allowsMockFallback } from "@/lib/ui-mode";
import type { RunBundle, RunNarrative } from "@/lib/mock-data/types";
import { Loader2, MessageCircle, Sparkles } from "lucide-react";
import { toast } from "sonner";

type ChatTurn = { role: "user" | "assistant"; content: string };

export function RunNarrativePanel({ runId, bundle }: { runId: string; bundle: RunBundle }) {
  const narrative: RunNarrative | undefined = bundle.narrative;
  const { data: live } = useApiHealth();
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (live) {
      api
        .chatThread(runId)
        .then((thread) => {
          if (cancelled) return;
          const turns = (thread.turns ?? [])
            .filter((t) => t.role === "user" || t.role === "assistant")
            .map((t) => ({
              role: t.role as "user" | "assistant",
              content: t.content,
            }));
          if (turns.length) setHistory(turns);
        })
        .catch(() => {});
    } else if (allowsMockFallback()) {
      const turns = getMockChatThread(runId);
      if (turns.length) setHistory(turns);
    }
    return () => {
      cancelled = true;
    };
  }, [runId, live]);

  const ask = async () => {
    const text = message.trim();
    if (!text || pending) return;
    setPending(true);
    setMessage("");
    const userTurn: ChatTurn = { role: "user", content: text };
    setHistory((h) => [...h, userTurn]);
    if (!live && allowsMockFallback()) {
      setHistory((h) => [...h, { role: "assistant", content: mockChatReply(text, bundle) }]);
      setPending(false);
      return;
    }
    try {
      const res = await api.chatRun(runId, text);
      setHistory((h) => [...h, { role: "assistant", content: res.reply }]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Chat failed");
      setHistory((h) => h.slice(0, -1));
    } finally {
      setPending(false);
    }
  };

  if (!narrative) {
    return (
      <Panel className="p-5 text-sm text-muted-foreground">
        No narrative for this run. Re-run with a current rehearse build or POST /api/backfill to
        regenerate analysis.json.
      </Panel>
    );
  }

  return (
    <div className="space-y-4">
      <Panel className="p-5 md:p-6 space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Sparkles className="size-4 text-primary" />
          <h2 className="font-display text-lg font-semibold">Run summary</h2>
          <Chip tone="neutral">{narrative.source === "llm+template" ? "AI + rules" : "Rules"}</Chip>
        </div>
        <p className="text-sm leading-relaxed">{narrative.executiveSummary}</p>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-xs text-muted-foreground mb-2">For founders / GTM</div>
            <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap font-sans text-sm">
              {narrative.forFounders}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-2">For engineering</div>
            <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap font-sans text-sm">
              {narrative.forEngineering}
            </div>
          </div>
        </div>
        {narrative.suggestedQuestions?.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground mb-2">Suggested review questions</div>
            <ul className="text-sm space-y-1 list-disc pl-5">
              {narrative.suggestedQuestions.map((q) => (
                <li key={q}>{q}</li>
              ))}
            </ul>
          </div>
        )}
      </Panel>

      <Panel className="p-5 md:p-6 space-y-3">
        <div className="flex items-center gap-2">
          <MessageCircle className="size-4" />
          <h3 className="font-display font-semibold">Ask about this run</h3>
          <span className="text-[11px] text-muted-foreground">
            {live
              ? "Uses LLM when API key is set; otherwise keyword hints"
              : "Offline demo — template replies from mock data"}
          </span>
        </div>
        {history.length > 0 && (
          <div className="space-y-3 max-h-64 overflow-y-auto border border-border rounded-lg p-3 bg-surface-2">
            {history.map((t, i) => (
              <div
                key={`${t.role}-${i}`}
                className={
                  t.role === "user"
                    ? "text-sm text-foreground"
                    : "text-sm text-muted-foreground border-l-2 border-primary/40 pl-3"
                }
              >
                <span className="text-[11px] uppercase font-mono text-muted-foreground mr-2">
                  {t.role}
                </span>
                <span className="whitespace-pre-wrap">{t.content}</span>
              </div>
            ))}
          </div>
        )}
        <div className="flex gap-2 flex-wrap">
          {(narrative.suggestedQuestions ?? []).slice(0, 2).map((q) => (
            <button
              key={q}
              type="button"
              className="text-[11px] px-2 py-1 rounded border border-border hover:bg-surface-2"
              onClick={() => setMessage(q)}
            >
              {q.length > 48 ? `${q.slice(0, 48)}…` : q}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 bg-surface border border-border rounded-md px-3 py-2 text-sm"
            placeholder="e.g. What blocked launch readiness?"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void ask();
              }
            }}
          />
          <button
            type="button"
            disabled={pending || !message.trim()}
            onClick={() => void ask()}
            className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50 inline-flex items-center gap-2"
          >
            {pending ? <Loader2 className="size-3.5 animate-spin" /> : null}
            Ask
          </button>
        </div>
      </Panel>
    </div>
  );
}
