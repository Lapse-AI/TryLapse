import { useEffect, useRef, useState } from "react";
import { Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import {
  Brain, Edit2, Check, X, Loader2, Sparkles,
  AlertTriangle, KeyRound, ChevronDown, ChevronUp, Eye, EyeOff,
} from "lucide-react";

type ProductModel = Record<string, unknown>;

type CrawlCredentials = {
  loginEmail: string;
  loginPassword: string;
  loginUrl: string;
  emailSelector: string;
  passwordSelector: string;
  submitSelector: string;
  llmApiKey: string;
  visionApiKey: string;
};

type Props = {
  live: boolean;
  targetUrl?: string;
  productName?: string;
  configId?: string | null;
  onModelReady?: (model: ProductModel) => void;
  onImportPersonas?: (personas: Array<{ id: string; name: string; role: string; goals: string[] }>) => void;
  onCredsChange?: (creds: CrawlCredentials) => void;
  startCollapsed?: boolean;
};

function SeverityChip({ s }: { s: string }) {
  const tone = s === "critical" ? "danger" : s === "moderate" ? "warn" : "neutral";
  return <Chip tone={tone}>{s}</Chip>;
}

const EMPTY_CREDS: CrawlCredentials = {
  loginEmail: "",
  loginPassword: "",
  loginUrl: "",
  emailSelector: "input[type='email'], input[name='email']",
  passwordSelector: "input[type='password']",
  submitSelector: "button[type='submit'], button:has-text('Login'), button:has-text('Sign in')",
  llmApiKey: "",
  visionApiKey: "",
};

export function ProductIntelligencePanel({ live, targetUrl, productName, configId, onModelReady, onImportPersonas, onCredsChange, startCollapsed }: Props) {
  const [model, setModel] = useState<ProductModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [expanded, setExpanded] = useState(!startCollapsed);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [showCreds, setShowCreds] = useState(false);
  const [creds, setCreds] = useState<CrawlCredentials>(EMPTY_CREDS);
  const [showPassword, setShowPassword] = useState(false);
  const [showLlmKey, setShowLlmKey] = useState(false);

  // Use ref so onModelReady is never a useEffect dependency (avoids re-render loop)
  const onModelReadyRef = useRef(onModelReady);
  useEffect(() => { onModelReadyRef.current = onModelReady; });

  useEffect(() => {
    if (!live) return;
    setLoading(true);
    api
      .getProductModel(configId)
      .then((m) => { setModel(m); onModelReadyRef.current?.(m); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [live, configId]); // onModelReady intentionally excluded — ref handles it

  const analyze = async () => {
    if (!live || !targetUrl) {
      toast.error("Start rehearse serve and set a target URL first");
      return;
    }
    setAnalyzing(true);
    const hasLogin = !!creds.loginEmail && !!creds.loginPassword;
    toast.info(
      hasLogin
        ? "Crawling with login credentials… takes 60–90 seconds"
        : "Crawling product… takes 30–60 seconds",
      { duration: 12000 }
    );
    try {
      const m = await api.analyzeProduct({
        targetUrl,
        productName,
        configId: configId || undefined,
        ...(hasLogin ? {
          auth: {
            loginUrl: creds.loginUrl || targetUrl,
            email: creds.loginEmail,
            password: creds.loginPassword,
            emailSelector: creds.emailSelector,
            passwordSelector: creds.passwordSelector,
            submitSelector: creds.submitSelector,
          }
        } : {}),
        ...(creds.llmApiKey ? { llmApiKey: creds.llmApiKey } : {}),
        ...(creds.visionApiKey ? { visionApiKey: creds.visionApiKey } : {}),
      });
      setModel(m);
      onModelReadyRef.current?.(m);
      toast.success(
        m.source === "llm"
          ? "Product analyzed with AI vision"
          : "Product analyzed (add LLM key for deeper analysis)",
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const saveEdit = async (field: string, value: string) => {
    if (!model) return;
    try {
      const m = await api.updateProductModel({ [field]: value }, configId);
      setModel({ ...model, ...m });
      toast.success("Saved");
    } catch {
      setModel({ ...model, [field]: value });
    }
    setEditingField(null);
  };

  const updateCred = (key: keyof CrawlCredentials, value: string) => {
    setCreds((prev) => {
      const next = { ...prev, [key]: value };
      onCredsChange?.(next);
      return next;
    });
  };

  const EditableText = ({ field, label }: { field: string; label: string }) => {
    const value = String(model?.[field] ?? "");
    const isEditing = editingField === field;
    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-muted-foreground font-medium">{label}</span>
          {!isEditing && (
            <button type="button" onClick={() => { setEditingField(field); setEditValue(value); }}
              className="p-1 rounded hover:bg-surface-2 text-muted-foreground">
              <Edit2 className="size-3" />
            </button>
          )}
        </div>
        {isEditing ? (
          <div className="flex gap-1">
            <textarea
              className="flex-1 text-sm bg-surface border border-border rounded-md px-2 py-1 min-h-[60px] focus:outline-none focus:ring-1 focus:ring-primary/30"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
            />
            <div className="flex flex-col gap-1">
              <button type="button" onClick={() => void saveEdit(field, editValue)}
                className="p-1.5 rounded bg-primary text-primary-foreground">
                <Check className="size-3" />
              </button>
              <button type="button" onClick={() => setEditingField(null)}
                className="p-1.5 rounded border border-border">
                <X className="size-3" />
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm">{value || <span className="text-muted-foreground italic">not set</span>}</p>
        )}
      </div>
    );
  };

  if (!live)
    return (
      <Panel className="p-5">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Brain className="size-4" /> Product intelligence — start rehearse serve to analyze
        </div>
      </Panel>
    );

  if (loading)
    return (
      <Panel className="p-5 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> Loading product model…
      </Panel>
    );

  return (
    <Panel className="overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-left hover:opacity-80 transition-opacity"
        >
          <Brain className="size-4 text-violet" />
          <span className="font-display font-semibold text-sm">Product intelligence</span>
          {model && (
            <Chip tone={model.source === "llm" ? "ready" : "neutral"}>
              {String(model.source ?? "")}
            </Chip>
          )}
          {model && !expanded && (
            <span className="text-[11px] text-muted-foreground font-normal ml-1 hidden sm:inline">
              {String(model.purpose ?? "").slice(0, 60)}{String(model.purpose ?? "").length > 60 ? "…" : ""}
            </span>
          )}
          {expanded ? <ChevronUp className="size-3.5 text-muted-foreground ml-1" /> : <ChevronDown className="size-3.5 text-muted-foreground ml-1" />}
        </button>
        <button
          type="button"
          disabled={analyzing || !targetUrl}
          onClick={() => void analyze()}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-violet/90 text-white disabled:opacity-40"
        >
          {analyzing ? <Loader2 className="size-3.5 animate-spin" /> : <Sparkles className="size-3.5" />}
          {analyzing ? "Analyzing…" : model ? "Re-analyze" : "Analyze product"}
        </button>
      </div>

      {/* Body — collapsible */}
      {expanded && <>

      {/* Crawl credentials collapsible */}
      <div className="border-b border-border">
        <button
          type="button"
          onClick={() => setShowCreds(!showCreds)}
          className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-muted-foreground hover:bg-surface-2/40"
        >
          <div className="flex items-center gap-1.5">
            <KeyRound className="size-3.5" />
            Crawl credentials & API keys
            {(creds.loginEmail || creds.llmApiKey) && (
              <span className="ml-1 px-1.5 py-0.5 rounded bg-primary/10 text-primary text-[10px]">configured</span>
            )}
          </div>
          {showCreds ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
        </button>

        {showCreds && (
          <div className="px-4 pb-4 pt-1 space-y-4 bg-surface/30">
            {/* Login credentials */}
            <div className="space-y-2">
              <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">
                Login credentials (if product requires auth)
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-muted-foreground">Email / Username</label>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={creds.loginEmail}
                    onChange={(e) => updateCred("loginEmail", e.target.value)}
                    className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={creds.loginPassword}
                      onChange={(e) => updateCred("loginPassword", e.target.value)}
                      className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 pr-7 focus:outline-none focus:ring-1 focus:ring-primary/30"
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-2 top-1/2 -translate-y-1/4 text-muted-foreground">
                      {showPassword ? <EyeOff className="size-3" /> : <Eye className="size-3" />}
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground">Login page URL (leave blank to auto-detect)</label>
                <input
                  type="url"
                  placeholder="https://example.com/login"
                  value={creds.loginUrl}
                  onChange={(e) => updateCred("loginUrl", e.target.value)}
                  className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                />
              </div>
              <details className="text-[11px] text-muted-foreground">
                <summary className="cursor-pointer hover:text-foreground">Advanced selectors (optional)</summary>
                <div className="mt-2 space-y-1.5">
                  <div>
                    <label>Email field selector</label>
                    <input type="text" value={creds.emailSelector}
                      onChange={(e) => updateCred("emailSelector", e.target.value)}
                      className="w-full mt-0.5 font-mono text-[10px] bg-surface border border-border rounded px-2 py-1 focus:outline-none" />
                  </div>
                  <div>
                    <label>Password field selector</label>
                    <input type="text" value={creds.passwordSelector}
                      onChange={(e) => updateCred("passwordSelector", e.target.value)}
                      className="w-full mt-0.5 font-mono text-[10px] bg-surface border border-border rounded px-2 py-1 focus:outline-none" />
                  </div>
                  <div>
                    <label>Submit button selector</label>
                    <input type="text" value={creds.submitSelector}
                      onChange={(e) => updateCred("submitSelector", e.target.value)}
                      className="w-full mt-0.5 font-mono text-[10px] bg-surface border border-border rounded px-2 py-1 focus:outline-none" />
                  </div>
                </div>
              </details>
            </div>

            {/* API keys */}
            <div className="space-y-2">
              <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">
                API keys for this crawl (optional — overrides server env)
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground">LLM API key (DeepSeek / OpenAI)</label>
                <div className="relative">
                  <input
                    type={showLlmKey ? "text" : "password"}
                    placeholder="sk-..."
                    value={creds.llmApiKey}
                    onChange={(e) => updateCred("llmApiKey", e.target.value)}
                    className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 pr-7 focus:outline-none focus:ring-1 focus:ring-primary/30"
                  />
                  <button type="button" onClick={() => setShowLlmKey(!showLlmKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/4 text-muted-foreground">
                    {showLlmKey ? <EyeOff className="size-3" /> : <Eye className="size-3" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground">Vision API key (if separate from LLM key)</label>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={creds.visionApiKey}
                  onChange={(e) => updateCred("visionApiKey", e.target.value)}
                  className="w-full mt-0.5 text-xs bg-surface border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Product model results */}
      {!model ? (
        <div className="p-8 text-center text-sm text-muted-foreground space-y-2">
          <Brain className="size-8 mx-auto opacity-30" />
          <p>
            Click "Analyze product" — the crawler will screenshot every page, use vision AI
            to understand the UI, and generate accurate personas + journeys.
          </p>
          <p className="text-[11px]">If the product requires login, expand "Crawl credentials" above first.</p>
        </div>
      ) : (
        <div className="p-5 space-y-5">
          <EditableText field="purpose" label="Purpose" />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Product type</div>
              <Chip tone="neutral">{String(model.product_type ?? "")}</Chip>
            </div>
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Technical surface</div>
              <div className="flex flex-wrap gap-1">
                {Object.entries((model.technical_surface as Record<string, boolean>) ?? {})
                  .filter(([, v]) => v)
                  .map(([k]) => (
                    <Chip key={k} tone="info">{k.replace("has_", "").replace("_", " ")}</Chip>
                  ))}
              </div>
            </div>
          </div>

          {Array.isArray(model.core_features) && model.core_features.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Core features</div>
              <div className="flex flex-wrap gap-1.5">
                {(model.core_features as string[]).map((f) => (
                  <Chip key={f} tone="neutral">{f}</Chip>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(model.primary_workflows) && model.primary_workflows.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2">Primary workflows detected</div>
              <div className="space-y-2">
                {(model.primary_workflows as Array<Record<string, string>>).slice(0, 5).map((w, i) => (
                  <div key={i} className="flex items-start justify-between gap-2 border border-border rounded-lg px-3 py-2">
                    <div>
                      <div className="text-sm font-medium">{w.name}</div>
                      <div className="text-[11px] text-muted-foreground">{w.description}</div>
                    </div>
                    <Chip tone="neutral">{w.frequency}</Chip>
                  </div>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(model.quality_concerns) && model.quality_concerns.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-2 flex items-center gap-1">
                <AlertTriangle className="size-3" /> Quality concerns observed
              </div>
              <div className="space-y-1.5">
                {(model.quality_concerns as Array<Record<string, string>>).map((c, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <SeverityChip s={c.severity} />
                    <span className="text-muted-foreground">[{c.area}]</span>
                    <span>{c.concern}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(model.user_types_observed) && model.user_types_observed.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="text-[11px] text-muted-foreground font-medium">
                  User types observed ({(model.user_types_observed as Array<Record<string, string>>).length})
                </div>
                {onImportPersonas && (
                  <button
                    type="button"
                    onClick={() => {
                      const userTypes = model.user_types_observed as Array<Record<string, string>>;
                      const personas = userTypes.map((u, i) => ({
                        id: `model-${i}-${(u.type ?? "user").toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")}`,
                        name: u.type ?? "User",
                        role: u.primary_goal ?? u.type ?? "user",
                        goals: [u.primary_goal ?? "", u.evidence ?? ""].filter(Boolean),
                      }));
                      onImportPersonas(personas);
                    }}
                    className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full border border-primary/30 text-primary hover:bg-primary/5 font-medium transition-colors"
                  >
                    <svg className="size-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M8 2v9M4 7l4 4 4-4M2 13h12" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    Import {(model.user_types_observed as Array<Record<string, string>>).length} as personas
                  </button>
                )}
              </div>
              <div className="space-y-1.5">
                {(model.user_types_observed as Array<Record<string, string>>).map((u, i) => (
                  <div key={i} className="border border-border rounded-xl px-3 py-2">
                    <div className="text-sm font-medium">{u.type}</div>
                    <div className="text-[11px] text-muted-foreground">{u.primary_goal}</div>
                    <div className="text-[10px] text-muted-foreground/70 mt-0.5 italic">{u.evidence}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      </>}
    </Panel>
  );
}
