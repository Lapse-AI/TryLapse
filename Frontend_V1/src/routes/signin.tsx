import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ShieldCheck, Loader2, Eye, EyeOff } from "lucide-react";
import { signIn } from "@/lib/test-auth";
import { getWorkspace } from "@/lib/workspace";
import { api } from "@/lib/api/client";
import { setWorkspace } from "@/lib/workspace";

export const Route = createFileRoute("/signin")({
  component: SignInPage,
});

function SignInPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError("Email and password are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await signIn(email, password);
      // Load workspace from API (JWT is now stored)
      const workspaces = await api.myWorkspaces();
      if (workspaces.length > 0) {
        setWorkspace(workspaces[0]);
        navigate({
          to: "/$workspaceSlug/dashboard",
          params: { workspaceSlug: workspaces[0].slug },
        });
      } else {
        navigate({ to: "/onboarding" });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("401") || msg.toLowerCase().includes("invalid")) {
        setError("Incorrect email or password.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle at 60% 20%, color-mix(in oklab, var(--primary) 6%, transparent), transparent 60%)",
        }}
      />
      <div className="relative w-full max-w-sm">
        {/* Brand */}
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <div className="size-9 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center">
            <ShieldCheck className="size-5 text-primary" />
          </div>
          <span className="font-display text-xl font-semibold tracking-tight">TryLapse</span>
        </div>

        <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8">
          <h1 className="font-display text-2xl font-semibold text-center mb-1">Welcome back</h1>
          <p className="text-sm text-muted-foreground text-center mb-6">
            Sign in to your workspace
          </p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="si-email" className="text-xs font-medium text-foreground/80">
                Work email
              </label>
              <input
                id="si-email"
                type="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                disabled={loading}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
              />
            </div>
            <div>
              <label htmlFor="si-password" className="text-xs font-medium text-foreground/80">
                Password
              </label>
              <div className="relative mt-1.5">
                <input
                  id="si-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className="w-full rounded-lg border border-border bg-background px-3.5 py-2.5 pr-10 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground disabled:opacity-50 transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-xs text-destructive bg-destructive/8 border border-destructive/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <div className="flex justify-end">
              <Link to="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
              style={{
                boxShadow:
                  "var(--shadow-primary, 0 2px 8px color-mix(in oklab, var(--primary) 30%, transparent))",
              }}
            >
              {loading && <Loader2 className="size-4 animate-spin" />}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          No account yet?{" "}
          <Link to="/signup" className="font-medium text-primary hover:underline">
            Create one →
          </Link>
        </p>
      </div>
    </div>
  );
}
