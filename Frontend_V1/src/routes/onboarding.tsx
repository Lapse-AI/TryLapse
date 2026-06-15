import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  ShieldCheck,
  Loader2,
  Building2,
  Rocket,
  CheckCircle2,
  Globe,
  ChevronRight,
  Search,
  Users,
  Check,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { setWorkspace } from "@/lib/workspace";

export const Route = createFileRoute("/onboarding")({
  component: OnboardingPage,
});

type Role = "founder" | "qa-lead" | "engineer" | "other";

const ROLES: { id: Role; label: string; desc: string }[] = [
  { id: "founder", label: "Founder / CEO", desc: "Building & launching the product" },
  { id: "qa-lead", label: "QA Lead", desc: "Owning quality and release readiness" },
  { id: "engineer", label: "Engineer", desc: "Shipping features and fixing bugs" },
  { id: "other", label: "Other", desc: "Something else entirely" },
];

// Persona suggestions keyed by role
const PERSONA_TEMPLATES: Record<Role, { id: string; label: string; desc: string }[]> = {
  founder: [
    { id: "power-user", label: "Power user", desc: "Pushes every feature to its limit" },
    { id: "new-signup", label: "New signup", desc: "First-time experience, zero context" },
    {
      id: "enterprise-eval",
      label: "Enterprise evaluator",
      desc: "Security-conscious, needs audit trail",
    },
    { id: "mobile-first", label: "Mobile-first user", desc: "Only uses the product on a phone" },
  ],
  "qa-lead": [
    {
      id: "regression-tester",
      label: "Regression tester",
      desc: "Systematically reruns known paths",
    },
    { id: "edge-case", label: "Edge-case explorer", desc: "Tries unusual inputs and flows" },
    { id: "accessibility", label: "A11y auditor", desc: "Navigates with keyboard & screen reader" },
    { id: "slow-network", label: "Slow network user", desc: "3G throttled, impatient" },
  ],
  engineer: [
    { id: "dev-dogfood", label: "Developer dogfooder", desc: "Uses dev-facing features and APIs" },
    { id: "new-signup", label: "New signup", desc: "First-time experience, zero context" },
    { id: "power-user", label: "Power user", desc: "Pushes every feature to its limit" },
    { id: "integrator", label: "Integration tester", desc: "Connects external tools and webhooks" },
  ],
  other: [
    { id: "new-signup", label: "New signup", desc: "First-time experience, zero context" },
    { id: "power-user", label: "Power user", desc: "Pushes every feature to its limit" },
    { id: "casual", label: "Casual visitor", desc: "Low intent, easily distracted" },
    { id: "mobile-first", label: "Mobile-first user", desc: "Only uses the product on a phone" },
  ],
};

function slugify(name: string): string {
  return (
    name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/[\s-]+/g, "-")
      .replace(/^-|-$/g, "") || "workspace"
  );
}

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2 justify-center mb-8">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all ${
            i < current ? "w-6 bg-primary" : i === current ? "w-8 bg-primary" : "w-6 bg-border"
          }`}
        />
      ))}
    </div>
  );
}

// Crawl simulation phases shown during the study step
const STUDY_PHASES = [
  "Connecting to your product…",
  "Crawling pages and navigation…",
  "Mapping user journeys…",
  "Identifying key flows…",
  "Generating persona recommendations…",
];

function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  // Step 0: Workspace + role
  const [workspaceName, setWorkspaceName] = useState("");
  const [role, setRole] = useState<Role | null>(null);

  // Step 1: Product
  const [productName, setProductName] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [urlStatus, setUrlStatus] = useState<"idle" | "checking" | "ok" | "fail">("idle");

  // Step 2: Study phase
  const [studyPhaseIdx, setStudyPhaseIdx] = useState(0);
  const [studyDone, setStudyDone] = useState(false);

  // Step 3: Personas
  const [selectedPersonas, setSelectedPersonas] = useState<Set<string>>(new Set());

  // Step 4: Create
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const slug = slugify(workspaceName);
  const personas = role ? PERSONA_TEMPLATES[role] : PERSONA_TEMPLATES.other;

  // When entering study step, kick off simulated crawl
  useEffect(() => {
    if (step !== 2) return;
    setStudyPhaseIdx(0);
    setStudyDone(false);

    // Fire real product analysis in background — non-blocking, fail silently
    if (productUrl.trim()) {
      api
        .analyzeProduct({
          targetUrl: productUrl.trim(),
          productName: productName.trim() || undefined,
        })
        .catch(() => {});
    }

    let idx = 0;
    const interval = setInterval(() => {
      idx++;
      if (idx < STUDY_PHASES.length) {
        setStudyPhaseIdx(idx);
      } else {
        clearInterval(interval);
        setStudyDone(true);
        // Pre-select all personas for this role
        const all = (role ? PERSONA_TEMPLATES[role] : PERSONA_TEMPLATES.other).map((p) => p.id);
        setSelectedPersonas(new Set(all));
      }
    }, 1400);

    return () => clearInterval(interval);
  }, [step, role]);

  const checkUrl = async () => {
    if (!productUrl.trim()) return;
    setUrlStatus("checking");
    try {
      const res = await api.preflight(productUrl.trim(), { allowLocalhost: true });
      setUrlStatus(res.ok ? "ok" : "fail");
    } catch {
      setUrlStatus("fail");
    }
  };

  const togglePersona = (id: string) => {
    setSelectedPersonas((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const finishOnboarding = async () => {
    setCreating(true);
    setCreateError(null);
    try {
      const ws = await api.createWorkspace({
        name: workspaceName,
        targetUrl: productUrl,
        productName: productName || workspaceName,
        teamRole: role ?? "other",
      });
      setWorkspace(ws);
      navigate({ to: "/init" });
    } catch {
      setCreateError("Failed to create workspace. Please try again.");
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle at 50% 20%, color-mix(in oklab, var(--primary) 5%, transparent), transparent 60%)",
        }}
      />
      <div className="relative w-full max-w-lg">
        {/* Brand */}
        <div className="flex items-center gap-2.5 justify-center mb-6">
          <div className="size-9 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center">
            <ShieldCheck className="size-5 text-primary" />
          </div>
          <span className="font-display text-xl font-semibold tracking-tight">TryLapse</span>
        </div>

        <StepIndicator current={step} total={5} />

        {/* ── Step 0: Workspace + Role ── */}
        {step === 0 && (
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8">
            <div className="flex items-center gap-2 mb-1">
              <Building2 className="size-4 text-primary" />
              <span className="text-xs font-medium text-primary uppercase tracking-wider">
                Step 1 of 5
              </span>
            </div>
            <h1 className="font-display text-2xl font-semibold mt-1 mb-1">Set up your workspace</h1>
            <p className="text-sm text-muted-foreground mb-6">
              Your workspace is where all your rehearsal runs, configs, and results live.
            </p>

            <div className="space-y-5">
              <div>
                <label className="text-xs font-medium text-foreground/80">
                  Company or workspace name
                </label>
                <input
                  type="text"
                  autoFocus
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="Acme Corp"
                  className="mt-1.5 w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/60"
                />
                {workspaceName.trim() && (
                  <p className="mt-1.5 text-[11px] text-muted-foreground font-mono">
                    app.trylapse.com/
                    <span className="text-primary font-semibold">{slug}</span>
                    /dashboard
                  </p>
                )}
              </div>

              <div>
                <label className="text-xs font-medium text-foreground/80 block mb-2">
                  Your role
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {ROLES.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setRole(r.id)}
                      className={`text-left rounded-xl border px-4 py-3 transition-all ${
                        role === r.id
                          ? "border-primary bg-primary/8 shadow-[0_0_0_2px_color-mix(in_oklab,var(--primary)_20%,transparent)]"
                          : "border-border hover:border-primary/40 hover:bg-surface-2"
                      }`}
                    >
                      <div className="text-sm font-medium">{r.label}</div>
                      <div className="text-[11px] text-muted-foreground mt-0.5">{r.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              type="button"
              disabled={!workspaceName.trim() || !role}
              onClick={() => setStep(1)}
              className="mt-6 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center justify-center gap-2"
            >
              Continue <ChevronRight className="size-4" />
            </button>
          </div>
        )}

        {/* ── Step 1: Product URL ── */}
        {step === 1 && (
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8">
            <div className="flex items-center gap-2 mb-1">
              <Globe className="size-4 text-primary" />
              <span className="text-xs font-medium text-primary uppercase tracking-wider">
                Step 2 of 5
              </span>
            </div>
            <h1 className="font-display text-2xl font-semibold mt-1 mb-1">About your product</h1>
            <p className="text-sm text-muted-foreground mb-6">
              TryLapse will crawl your product and set up journeys automatically.
            </p>

            <div className="space-y-5">
              <div>
                <label className="text-xs font-medium text-foreground/80">Product name</label>
                <input
                  type="text"
                  autoFocus
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="Acme App"
                  className="mt-1.5 w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/60"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-foreground/80">
                  Product URL
                  <span className="ml-1 font-normal text-muted-foreground">
                    (staging or production)
                  </span>
                </label>
                <div className="mt-1.5 flex gap-2">
                  <input
                    type="url"
                    value={productUrl}
                    onChange={(e) => {
                      setProductUrl(e.target.value);
                      setUrlStatus("idle");
                    }}
                    onBlur={checkUrl}
                    placeholder="https://app.example.com"
                    className="flex-1 rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/60"
                  />
                  <button
                    type="button"
                    onClick={checkUrl}
                    disabled={!productUrl.trim() || urlStatus === "checking"}
                    className="rounded-lg border border-border px-3.5 py-2.5 text-sm text-muted-foreground hover:bg-surface-2 disabled:opacity-40"
                  >
                    {urlStatus === "checking" ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      "Check"
                    )}
                  </button>
                </div>
                {urlStatus === "ok" && (
                  <p className="mt-1.5 text-xs text-ready flex items-center gap-1">
                    <CheckCircle2 className="size-3.5" /> Reachable — ready to study
                  </p>
                )}
                {urlStatus === "fail" && (
                  <p className="mt-1.5 text-xs text-warn">
                    Could not reach this URL. You can still continue — agents will retry on first
                    run.
                  </p>
                )}
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={() => setStep(0)}
                className="rounded-lg border border-border px-4 py-2.5 text-sm text-muted-foreground hover:bg-surface-2"
              >
                Back
              </button>
              <button
                type="button"
                disabled={!productName.trim() || !productUrl.trim()}
                onClick={() => setStep(2)}
                className="flex-1 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center justify-center gap-2"
              >
                Study my product <ChevronRight className="size-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Studying product ── */}
        {step === 2 && (
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8">
            <div className="flex items-center gap-2 mb-1">
              <Search className="size-4 text-primary" />
              <span className="text-xs font-medium text-primary uppercase tracking-wider">
                Step 3 of 5
              </span>
            </div>
            <h1 className="font-display text-2xl font-semibold mt-1 mb-2">Studying your product</h1>
            <p className="text-sm text-muted-foreground mb-6">
              TryLapse agents are crawling{" "}
              <span className="font-mono text-foreground text-xs">{productUrl}</span> to map
              journeys and prepare persona configs.
            </p>

            <div className="rounded-xl border border-border bg-background p-5 space-y-3 mb-6">
              {STUDY_PHASES.map((phase, i) => {
                const done = i < studyPhaseIdx || studyDone;
                const active = i === studyPhaseIdx && !studyDone;
                return (
                  <div key={phase} className="flex items-center gap-3">
                    <div
                      className={`size-5 rounded-full flex items-center justify-center shrink-0 ${
                        done ? "bg-ready/15 text-ready" : active ? "bg-primary/10" : "bg-border/40"
                      }`}
                    >
                      {done ? (
                        <Check className="size-3" />
                      ) : active ? (
                        <Loader2 className="size-3 animate-spin text-primary" />
                      ) : (
                        <span className="size-1.5 rounded-full bg-muted-foreground/30" />
                      )}
                    </div>
                    <span
                      className={`text-sm ${done ? "text-foreground" : active ? "text-foreground" : "text-muted-foreground/50"}`}
                    >
                      {phase}
                    </span>
                  </div>
                );
              })}
            </div>

            {studyDone ? (
              <button
                type="button"
                onClick={() => setStep(3)}
                className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              >
                Review personas <ChevronRight className="size-4" />
              </button>
            ) : (
              <div className="text-center text-xs text-muted-foreground">
                This takes about 7 seconds…
              </div>
            )}
          </div>
        )}

        {/* ── Step 3: Persona selection ── */}
        {step === 3 && (
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8">
            <div className="flex items-center gap-2 mb-1">
              <Users className="size-4 text-primary" />
              <span className="text-xs font-medium text-primary uppercase tracking-wider">
                Step 4 of 5
              </span>
            </div>
            <h1 className="font-display text-2xl font-semibold mt-1 mb-1">Suggested personas</h1>
            <p className="text-sm text-muted-foreground mb-6">
              Based on your product and role, we've suggested these synthetic users. Deselect any
              you don't need — you can always add more later.
            </p>

            <div className="space-y-2 mb-6">
              {personas.map((p) => {
                const selected = selectedPersonas.has(p.id);
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => togglePersona(p.id)}
                    className={`w-full text-left rounded-xl border px-4 py-3 flex items-start gap-3 transition-all ${
                      selected
                        ? "border-primary bg-primary/6"
                        : "border-border hover:border-primary/30 hover:bg-surface-2"
                    }`}
                  >
                    <div
                      className={`size-5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 ${
                        selected ? "bg-primary border-primary" : "border-border"
                      }`}
                    >
                      {selected && <Check className="size-3 text-primary-foreground" />}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{p.label}</div>
                      <div className="text-[11px] text-muted-foreground mt-0.5">{p.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>

            <p className="text-[11px] text-muted-foreground mb-4">
              {selectedPersonas.size} of {personas.length} personas selected
            </p>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="rounded-lg border border-border px-4 py-2.5 text-sm text-muted-foreground hover:bg-surface-2"
              >
                Back
              </button>
              <button
                type="button"
                disabled={selectedPersonas.size === 0}
                onClick={() => setStep(4)}
                className="flex-1 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center justify-center gap-2"
              >
                Confirm personas <ChevronRight className="size-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 4: Launch ── */}
        {step === 4 && (
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <Rocket className="size-4 text-primary" />
              <span className="text-xs font-medium text-primary uppercase tracking-wider">
                Step 5 of 5
              </span>
            </div>
            <h1 className="font-display text-2xl font-semibold mt-1 mb-1">
              You're ready to rehearse
            </h1>
            <p className="text-sm text-muted-foreground mb-6">
              Your workspace will be created with {selectedPersonas.size} persona
              {selectedPersonas.size !== 1 ? "s" : ""}. Your dashboard will be empty until you
              trigger your first run.
            </p>

            <div className="rounded-xl border border-border bg-background p-5 text-left space-y-3 mb-6">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Workspace</span>
                <span className="font-medium">{workspaceName}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">URL slug</span>
                <span className="font-mono text-primary text-xs">{slug}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Product</span>
                <span className="font-medium">{productName}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Target URL</span>
                <span className="font-mono text-xs truncate max-w-[180px]">{productUrl}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Role</span>
                <span className="font-medium capitalize">
                  {ROLES.find((r) => r.id === role)?.label}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Personas</span>
                <span className="font-medium">{selectedPersonas.size} configured</span>
              </div>
            </div>

            {createError && (
              <p className="text-xs text-destructive bg-destructive/8 border border-destructive/20 rounded-lg px-3 py-2 mb-4">
                {createError}
              </p>
            )}

            <div className="flex flex-col gap-3">
              <button
                type="button"
                disabled={creating}
                onClick={finishOnboarding}
                className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
                style={{
                  boxShadow:
                    "var(--shadow-primary, 0 2px 8px color-mix(in oklab, var(--primary) 30%, transparent))",
                }}
              >
                {creating ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Setting up workspace…
                  </>
                ) : (
                  <>
                    <Rocket className="size-4" /> Launch dashboard
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                disabled={creating}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                ← Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
