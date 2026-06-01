import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Play, Search, ChevronDown, Check, Loader2, Menu } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { AppSidebar } from "@/components/app-sidebar";
import {
  useApiHealth,
  useScopedRunSummaries,
  useSearch,
  useTriggerJob,
  useWorkspace,
} from "@/lib/api/hooks";
import { uiModeLabel } from "@/lib/ui-mode";
import { TestGroupAuth } from "@/components/test-group-auth";
import { useTestGroup, displayTargetForGroup } from "@/hooks/use-test-group";

const ENVS = [
  { id: "prod-canary", label: "prod-canary", hint: "Production canary slice" },
  { id: "staging", label: "staging", hint: "Pre-prod mirror" },
  { id: "demo", label: "demo", hint: "Sandbox tenant" },
];

export function RehearseTopBar() {
  const { data: live } = useApiHealth();
  const { data: workspace } = useWorkspace();
  const { data: summaries = [] } = useScopedRunSummaries();
  const trigger = useTriggerJob();
  const { group } = useTestGroup();
  const [env, setEnv] = useState(workspace?.env ?? "staging");
  const [query, setQuery] = useState("");
  const [showResults, setShowResults] = useState(false);
  const { data: searchResults } = useSearch(query);

  const host = displayTargetForGroup(group);
  const slug = workspace?.slug ?? "workspace";

  const runJob = (mode: "run" | "crawl") => {
    trigger.mutate({ mode, noCrawl: mode === "run" ? false : undefined });
  };

  return (
    <header className="h-14 border-b border-border bg-surface/60 backdrop-blur flex items-center px-3 md:px-6 gap-3">
      <MobileNav />
      <div className="hidden md:flex items-center gap-2 text-xs font-mono text-muted-foreground">
        <span className="px-2 py-0.5 rounded bg-surface-2 border border-border">{slug}</span>
        <span>/</span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              aria-label={`Environment: ${env}`}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-border bg-surface-2 hover:bg-surface-3 text-foreground"
            >
              {env} <ChevronDown className="size-3 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuLabel>Environment</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {ENVS.map((e) => (
              <DropdownMenuItem
                key={e.id}
                onSelect={() => setEnv(e.id)}
                className="flex items-start gap-2"
              >
                <Check
                  className={`size-3.5 mt-0.5 ${e.id === env ? "opacity-100" : "opacity-0"}`}
                />
                <div>
                  <div className="text-sm">{e.label}</div>
                  <div className="text-[11px] text-muted-foreground">{e.hint}</div>
                </div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <span>/</span>
        <span className="text-foreground">{host}</span>
        {live ? (
          <span className="text-ready text-[10px]">· API live</span>
        ) : (
          <span className="text-warn text-[10px]">· mock data</span>
        )}
        <span className="text-[10px] px-1.5 py-0.5 rounded border border-violet/30 text-violet">
          Vision UI · {uiModeLabel()}
        </span>
      </div>

      <div className="flex-1 max-w-md relative">
        <Search className="size-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          aria-label="Search runs, issues, pages"
          placeholder="Search runs, issues, pages…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowResults(true);
          }}
          onFocus={() => setShowResults(true)}
          onBlur={() => setTimeout(() => setShowResults(false), 150)}
          className="w-full bg-surface border border-border rounded-md pl-8 pr-3 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
        />
        {showResults && query.length >= 2 && searchResults && (
          <div className="absolute top-full left-0 right-0 mt-1 z-50 border border-border rounded-md bg-surface shadow-lg max-h-64 overflow-y-auto text-sm">
            {searchResults.runs.length === 0 &&
            searchResults.issues.length === 0 &&
            searchResults.pages.length === 0 ? (
              <div className="p-3 text-muted-foreground text-xs">No matches</div>
            ) : (
              <>
                {searchResults.runs.map((r) => (
                  <Link
                    key={r.id}
                    to="/runs/$runId"
                    params={{ runId: r.id }}
                    className="block px-3 py-2 hover:bg-surface-2 font-mono text-xs"
                  >
                    run · {r.id}
                  </Link>
                ))}
                {searchResults.issues
                  .slice(0, 5)
                  .map((i: { id: string; title: string; runId: string }) => (
                    <Link
                      key={i.id}
                      to="/runs/$runId"
                      params={{ runId: i.runId }}
                      className="block px-3 py-2 hover:bg-surface-2 text-xs truncate"
                    >
                      issue · {i.title}
                    </Link>
                  ))}
              </>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <TestGroupAuth />
        <button
          type="button"
          disabled={!live || trigger.isPending}
          onClick={() => runJob("crawl")}
          className="hidden sm:inline-flex text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 disabled:opacity-50"
        >
          Crawl only
        </button>
        <button
          type="button"
          disabled={!live || trigger.isPending}
          onClick={() => runJob("run")}
          className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 inline-flex items-center gap-1.5 font-medium disabled:opacity-50"
        >
          {trigger.isPending ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Play className="size-3.5" />
          )}
          Run rehearsal
        </button>
        {!live && (
          <Link to="/cli" className="text-[10px] text-muted-foreground hidden lg:inline">
            start API
          </Link>
        )}
      </div>
    </header>
  );
}

function MobileNav() {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          aria-label="Open navigation"
          className="md:hidden inline-flex items-center justify-center size-9 rounded-md border border-border hover:bg-surface-2"
        >
          <Menu className="size-4" />
        </button>
      </SheetTrigger>
      <SheetContent side="left" className="p-0 w-72">
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <div onClick={() => setOpen(false)}>
          <AppSidebar />
        </div>
      </SheetContent>
    </Sheet>
  );
}
