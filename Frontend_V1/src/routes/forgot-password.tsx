import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ShieldCheck, Loader2, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api/client";

export const Route = createFileRoute("/forgot-password")({
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError("Email is required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.forgotPassword(email);
      setSubmitted(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
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
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="size-12 rounded-full bg-ready/15 border border-ready/25 flex items-center justify-center">
                <CheckCircle2 className="size-6 text-ready" />
              </div>
            </div>
            <h1 className="font-display text-2xl font-semibold mb-2">Check your email</h1>
            <p className="text-sm text-muted-foreground mb-6">
              We've sent a password reset link to <span className="font-medium">{email}</span>. Click the link to create a new password.
            </p>
            <p className="text-xs text-muted-foreground mb-6">
              The link expires in 24 hours.
            </p>
            <div className="space-y-3">
              <button
                onClick={() => {
                  setSubmitted(false);
                  setEmail("");
                }}
                className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                Try another email
              </button>
              <Link
                to="/signin"
                className="w-full rounded-lg border border-border px-4 py-2.5 text-sm font-semibold text-foreground hover:bg-surface-2 transition-colors inline-block text-center"
              >
                Back to sign in
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <div className="size-9 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center">
            <ShieldCheck className="size-5 text-primary" />
          </div>
          <span className="font-display text-xl font-semibold tracking-tight">TryLapse</span>
        </div>

        <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8">
          <h1 className="font-display text-2xl font-semibold text-center mb-1">Reset your password</h1>
          <p className="text-sm text-muted-foreground text-center mb-6">
            Enter your email to receive a password reset link
          </p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="fp-email" className="text-xs font-medium text-foreground/80">
                Work email
              </label>
              <input
                id="fp-email"
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
              {loading ? "Sending…" : "Send reset link"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Remember your password?{" "}
          <Link to="/signin" className="font-medium text-primary hover:underline">
            Sign in →
          </Link>
        </p>
      </div>
    </div>
  );
}
