import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ShieldCheck, Loader2 } from "lucide-react";
import { signUp } from "@/lib/test-auth";

export const Route = createFileRoute("/signup")({
  component: SignUpPage,
});

function SignUpPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError("Email and password are required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await signUp(name, email, password);
      navigate({ to: "/onboarding" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("409") || msg.toLowerCase().includes("already")) {
        setError("An account with that email already exists. Try signing in.");
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
            "radial-gradient(circle at 40% 30%, color-mix(in oklab, var(--primary) 6%, transparent), transparent 60%)",
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
          <h1 className="font-display text-2xl font-semibold text-center mb-1">
            Create your account
          </h1>
          <p className="text-sm text-muted-foreground text-center mb-6">
            Start rehearsing your product in minutes
          </p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="su-name" className="text-xs font-medium text-foreground/80">
                Your name
              </label>
              <input
                id="su-name"
                type="text"
                autoComplete="name"
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jane Smith"
                disabled={loading}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
              />
            </div>
            <div>
              <label htmlFor="su-email" className="text-xs font-medium text-foreground/80">
                Work email
              </label>
              <input
                id="su-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                disabled={loading}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
              />
            </div>
            <div>
              <label htmlFor="su-password" className="text-xs font-medium text-foreground/80">
                Password
                <span className="ml-1 text-muted-foreground font-normal">(min 8 characters)</span>
              </label>
              <input
                id="su-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
              />
            </div>

            {error && (
              <p className="text-xs text-destructive bg-destructive/8 border border-destructive/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

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
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-xs text-muted-foreground text-center mt-4">
            By creating an account you agree to our terms of service.
          </p>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Already have an account?{" "}
          <Link to="/signin" className="font-medium text-primary hover:underline">
            Sign in →
          </Link>
        </p>
      </div>
    </div>
  );
}
