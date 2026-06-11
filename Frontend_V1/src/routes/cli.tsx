import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, UnderConstruction } from "@/components/ui-bits";
import { Copy } from "lucide-react";

export const Route = createFileRoute("/cli")({
  head: () => ({ meta: [{ title: "CLI — Launch Rehearsal" }] }),
  component: CliPage,
});

const commands = [
  {
    cmd: "rehearse run -c config.yaml -o artifacts",
    status: "shipped" as const,
    desc: "Crawl + journeys + multi-agent + scorecard",
  },
  {
    cmd: "rehearse crawl -c config.yaml -o artifacts",
    status: "shipped" as const,
    desc: "Crawl only — sitemap.json + sitemap.md + workflow graph",
  },
  {
    cmd: "rehearse scorecard -e runs/<id>.json -c config.yaml",
    status: "shipped" as const,
    desc: "Regenerate scorecard from saved evidence JSON",
  },
  {
    cmd: "rehearse serve -o artifacts [--port 8765]",
    status: "shipped" as const,
    desc: "Local monitoring dashboard — GET /api/runs, /api/diff, /files/*",
  },
  {
    cmd: "rehearse diff <run-a> <run-b> -o artifacts",
    status: "shipped" as const,
    desc: "Compare two runs — readiness, sitemap, step outcomes",
  },
  {
    cmd: "rehearse run --llm --no-crawl",
    status: "shipped" as const,
    desc: "LLM persona agents via NVIDIA NIM or OpenAI-compatible API",
  },
  {
    cmd: "rehearse init <url>",
    status: "planned" as const,
    desc: "Scaffold rehearse.yaml from a target URL",
  },
  {
    cmd: "rehearse schedule",
    status: "planned" as const,
    desc: "Cron wrapper — schedule recurring rehearsals",
  },
];

const example = `$ cd launch-rehearsal && rehearse run -c examples/cal-com-phase0.yaml -o artifacts --llm

Preflight OK: https://cal.com (200)
LLM provider: nvidia_nim
▸ Crawler        done   84s   48 pages
▸ Workflow       done   47s   4 workflows, 1 suggested journey
▸ Journey runner done  318s   5 journeys · 14 steps · 0 flaky
▸ Persona ×3     done  120s   heuristic findings
▸ LLM persona ×3 done   42s   narrative analysis
▸ Synthesizer    done   22s   merged → 5 issues · readiness Amber

{
  "run_id": "cal-20260529-193724",
  "readiness": "Amber",
  "issues": 5,
  "delights": 3,
  "scorecard": "artifacts/scorecards/cal-20260529-193724-scorecard.md",
  "evidence": "artifacts/runs/cal-20260529-193724.json"
}

$ rehearse serve -o artifacts
Launch Rehearsal dashboard → http://127.0.0.1:8765`;

function CliPage() {
  return (
    <UnderConstruction>
    <div>
      <PageHeader
        eyebrow="ship"
        title="rehearse — CLI reference"
        description="The CLI ships today. This dashboard reads the same artifacts the CLI writes under artifacts/."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-5">
          <div className="text-xs text-muted-foreground mb-2">Install (from TryLapse repo)</div>
          <div className="bg-surface-2/50 border border-border rounded-lg p-4 flex items-center justify-between font-mono text-sm">
            <span>
              <span className="text-muted-foreground">$</span> cd launch-rehearsal && pip install -e
              . && playwright install chromium
            </span>
            <button type="button" className="text-muted-foreground hover:text-foreground">
              <Copy className="size-4" />
            </button>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            From repo root:{" "}
            <span className="font-mono">
              ./rehearse run -c launch-rehearsal/examples/cal-com-phase0.yaml
            </span>
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border">
            <div className="text-xs text-muted-foreground">Commands</div>
            <div className="font-display text-lg font-semibold mt-0.5">
              {commands.length} total · {commands.filter((c) => c.status === "shipped").length}{" "}
              shipped
            </div>
          </div>
          <div className="divide-y divide-border">
            {commands.map((c) => (
              <div
                key={c.cmd}
                className="p-4 flex items-center justify-between hover:bg-surface-2/30 gap-4"
              >
                <div className="min-w-0">
                  <code className="font-mono text-sm text-primary break-all">{c.cmd}</code>
                  <div className="text-xs text-muted-foreground mt-1">{c.desc}</div>
                </div>
                <Chip tone={c.status === "shipped" ? "ready" : "violet"}>{c.status}</Chip>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="text-xs text-muted-foreground">Example output</div>
            <Chip>rehearse run + serve</Chip>
          </div>
          <pre className="p-5 text-[12.5px] font-mono leading-relaxed overflow-x-auto bg-surface-2/30 text-foreground/95 whitespace-pre">
            {example}
          </pre>
        </Panel>

        <Panel className="p-5">
          <div className="text-xs text-muted-foreground mb-2">
            Artifact layout (backend contract)
          </div>
          <pre className="text-xs font-mono text-muted-foreground">{`artifacts/
  runs/<run_id>.json          # step evidence
  scorecards/<run_id>-scorecard.md
  sitemaps/<run_id>-sitemap.json
  sitemaps/<run_id>-sitemap.md
  artifacts/<run_id>/*.png    # screenshots
  analysis/<run_id>.json     # structured issues + narrative
  chats/<run_id>.json        # persistent run chat threads`}</pre>
        </Panel>

        <Panel className="p-5">
          <div className="text-xs text-muted-foreground mb-3">Dashboard API (rehearse serve)</div>
          <ul className="text-sm font-mono space-y-2">
            <li>GET /api/trends — readiness/pages/flake + narrative insight</li>
            <li>GET /api/digest?n=7 — command center digest</li>
            <li>GET/POST /api/runs/&#123;id&#125;/chat — run Q&amp;A thread</li>
            <li>GET /api/diff?a=&amp;b= — compare runs + “What changed” narrative</li>
            <li>POST /api/recordings/compile — journey recorder → YAML fragment</li>
            <li>
              POST /api/configs — init wizard YAML write (viewports,
              execute_all_personas_in_browser)
            </li>
            <li>POST /api/jobs — background run/crawl (llm flag supported)</li>
          </ul>
        </Panel>
      </div>
    </div>
    </UnderConstruction>
  );
}
