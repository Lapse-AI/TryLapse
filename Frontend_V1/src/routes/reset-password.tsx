import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { ShieldCheck, Loader2, Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api/client";

export const Route = createFileRoute("/reset-password")({
  component: ResetPasswordPage,
  validateSearch: (search: Record<string, unknown>) => ({
    token: search.token as string | undefined,
  }),
});

function ResetPasswordPage() {
  const navigate = useNavigate();
  const { token } = useSearch({ from: Route.id });
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token. Please request a new password reset link.");
    }
  }, [token]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || !confirmPassword) {
      setError("Both password fields are required.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.resetPassword(token!, password);
      setSuccess(true);
      setTimeout(() => {
        navigate({ to: "/signin" });
      }, 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("401")) {
        setError("This reset link has expired or is invalid. Please request a new one.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="relative w-full max-w-sm">
          <div className="rounded-2xl border border-border bg-surface shadow-xl shadow-black/5 p-8 text-center">
            <h1 className="font-display text-2xl font-semibold mb-2">Invalid link</h1>
            <p className="text-sm text-muted-foreground mb-6">
              This password reset link is invalid or missing. Please request a new one.
            </p>
            <Link
              to="/forgot-password"
              className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity inline-block"
            >
              Request new link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
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
            <h1 className="font-display text-2xl font-semibold mb-2">Password reset successful</h1>
            <p className="text-sm text-muted-foreground mb-6">
              Your password has been changed. Redirecting to sign in...
            </p>
            <div className="flex justify-center">
              <Loader2 className="size-5 animate-spin text-primary" />
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
          <h1 className="font-display text-2xl font-semibold text-center mb-1">Create new password</h1>
          <p className="text-sm text-muted-foreground text-center mb-6">
            Enter a strong password to secure your account
          </p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="rp-password" className="text-xs font-medium text-foreground/80">
                New password
              </label>
              <div className="relative mt-1.5">
                <input
                  id="rp-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
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

            <div>
              <label htmlFor="rp-confirm" className="text-xs font-medium text-foreground/80">
                Confirm password
              </label>
              <div className="relative mt-1.5">
                <input
                  id="rp-confirm"
                  type={showConfirmPassword ? "text" : "password"}
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className="w-full rounded-lg border border-border bg-background px-3.5 py-2.5 pr-10 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={loading}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground disabled:opacity-50 transition-colors"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
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
              {loading ? "Resetting…" : "Reset password"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          <Link to="/signin" className="font-medium text-primary hover:underline">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
