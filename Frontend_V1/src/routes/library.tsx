import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useLibrary, useApiHealth } from "@/lib/api/hooks";
import { api } from "@/lib/api/client";
import { useLatestRun } from "@/lib/api/hooks";

export const Route = createFileRoute("/library")({
  head: () => ({ meta: [{ title: "Journey library — Launch Rehearsal" }] }),
  component: LibraryPage,
});

function LibraryPage() {
  const { data: live } = useApiHealth();
  const { data: library } = useLibrary();
  const latest = useLatestRun();

  return (
    <div>
      <PageHeader
        eyebrow="map"
        title="Journey library & templates"
        description="Example configs, workflow-suggested journeys, parallel seeds, and FLAKY detection settings."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Panel className="p-4">
            <div className="text-xs text-muted-foreground">Parallel seeds</div>
            <div className="font-display text-lg font-semibold mt-1 text-ready">
              {library?.parallelSeeds ? "enabled" : "—"}
            </div>
          </Panel>
          <Panel className="p-4">
            <div className="text-xs text-muted-foreground">Flaky config</div>
            <div className="font-display text-lg font-semibold mt-1 text-ready">
              {library?.flakyConfig ? "enabled" : "—"}
            </div>
          </Panel>
          <Panel className="p-4">
            <div className="text-xs text-muted-foreground">Templates</div>
            <div className="font-display text-lg font-semibold mt-1">
              {library?.templates.length ?? 0}
            </div>
          </Panel>
          <Panel className="p-4">
            <div className="text-xs text-muted-foreground">Suggested</div>
            <div className="font-display text-lg font-semibold mt-1">
              {library?.suggested.length ?? 0}
            </div>
          </Panel>
        </div>

        {latest && live && (
          <Panel className="p-5">
            <div className="text-sm font-medium mb-2">GraphML sitemap export</div>
            <a
              href={api.graphmlUrl(latest.id)}
              className="text-xs text-primary font-mono hover:underline"
              download
            >
              GET /api/sitemap/{latest.id}/graphml
            </a>
          </Panel>
        )}

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border font-display font-semibold">Templates</div>
          <div className="divide-y divide-border">
            {(library?.templates ?? []).map((t) => (
              <div key={t.id} className="p-5 flex items-start justify-between gap-4">
                <div>
                  <div className="font-medium">{t.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">{t.reason}</div>
                  <Chip tone="info">{t.category}</Chip>
                </div>
                {t.configPath && (
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {t.configPath}
                  </span>
                )}
              </div>
            ))}
            {!library && !live && (
              <div className="p-8 text-sm text-muted-foreground text-center">
                Connect API for live library data.
              </div>
            )}
          </div>
        </Panel>

        {(library?.suggested ?? []).length > 0 && (
          <Panel className="overflow-hidden">
            <div className="p-5 border-b border-border font-display font-semibold">
              Workflow-suggested journeys
            </div>
            <div className="divide-y divide-border">
              {(library!.suggested as { id: string; title: string; reason: string }[]).map((s) => (
                <div key={s.id} className="p-5">
                  <div className="font-medium">{s.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">{s.reason}</div>
                </div>
              ))}
            </div>
          </Panel>
        )}

        <div className="text-sm text-muted-foreground">
          <Link to="/init" className="text-primary hover:underline">
            Init wizard
          </Link>{" "}
          · OpenAPI / sitemap.xml seed import via CLI config (Phase 2 UI)
        </div>
      </div>
    </div>
  );
}
