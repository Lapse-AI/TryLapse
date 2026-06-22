import { useEffect, useState } from "react";
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { ShieldCheck, Loader2 } from "lucide-react";
import { api } from "@/lib/api/client";
import { getTestUser, signIn, signUp } from "@/lib/test-auth";
import { setWorkspace } from "@/lib/workspace";

export const Route = createFileRoute("/join/$token")({
  component: JoinPage,
});

type InviteInfo = Awaited<ReturnType<typeof api.getInvite>>;

function JoinPage() {
  const { token } = useParams({ from: "/join/$token" });
  const navigate = useNavigate();
  const [invite, setInvite] = useState<InviteInfo | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const alreadySignedIn = !!getTestUser();

  useEffect(() => {
    api
      .getInvite(token)
      .then(setInvite)
      .catch(() => setLoadError("This invite link is invalid or has expired."));
  }, [token]);

  async function joinWorkspace() {
    try {
      await api.acceptInvite(token);
      const workspaces = await api.myWorkspaces();
      const joined = workspaces.find((w) => w.slug === invite?.workspaceSlug) ?? workspaces[0];
      if (joined) {
        setWorkspace(joined);
        navigate({ to: "/$workspaceSlug/dashboard", params: { workspaceSlug: joined.slug } });
      } else {
        navigate({ to: "/onboarding" });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      setSubmitError(
        msg.includes("409") ? "This invite has already been used." : "Failed to join workspace.",
      );
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!invite) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      if (mode === "signup") {
        await signUp(name, invite.email, password);
      } else {
        await signIn(invite.email, password);
      }
      await joinWorkspace();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      setSubmitError(
        mode === "signup"
          ? "Could not create account — try signing in instead if you already have one."
          : msg.toLowerCase().includes("invalid")
            ? "Incorrect password."
            : "Sign-in failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="max-w-sm text-center space-y-2">
          <h1 className="font-display text-xl font-semibold">Invite not found</h1>
          <p className="text-sm text-muted-foreground">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!invite) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (invite.acceptedAt) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="max-w-sm text-center space-y-2">
          <h1 className="font-display text-xl font-semibold">Already accepted</h1>
          <p className="text-sm text-muted-foreground">
            This invite to {invite.workspaceName ?? "the workspace"} has already been used.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-sm w-full space-y-6">
        <div className="text-center space-y-2">
          <div className="size-10 rounded-lg bg-primary/15 border border-primary/25 flex items-center justify-center mx-auto">
            <ShieldCheck className="size-5 text-primary" />
          </div>
          <h1 className="font-display text-xl font-semibold">
            Join {invite.workspaceName ?? "workspace"}
          </h1>
          <p className="text-sm text-muted-foreground">
            You've been invited as <span className="font-medium">{invite.role}</span> —{" "}
            {invite.email}
          </p>
        </div>

        {alreadySignedIn ? (
          <button
            type="button"
            onClick={joinWorkspace}
            className="w-full px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90"
          >
            Join workspace
          </button>
        ) : (
          <>
            <div className="flex rounded-lg border border-border p-1 text-sm">
              <button
                type="button"
                onClick={() => setMode("signup")}
                className={`flex-1 py-1.5 rounded-md ${mode === "signup" ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}
              >
                Create account
              </button>
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`flex-1 py-1.5 rounded-md ${mode === "login" ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}
              >
                I have an account
              </button>
            </div>

            <form onSubmit={submit} className="space-y-3">
              {mode === "signup" && (
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full h-10 px-3 rounded-md border border-border bg-background text-sm"
                />
              )}
              <input
                type="email"
                value={invite.email}
                disabled
                className="w-full h-10 px-3 rounded-md border border-border bg-surface-2 text-sm text-muted-foreground"
              />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "signup" ? "Choose a password (8+ characters)" : "Password"}
                className="w-full h-10 px-3 rounded-md border border-border bg-background text-sm"
              />
              {submitError && <div className="text-xs text-danger">{submitError}</div>}
              <button
                type="submit"
                disabled={submitting}
                className="w-full px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50"
              >
                {submitting
                  ? "Joining…"
                  : mode === "signup"
                    ? "Create account & join"
                    : "Sign in & join"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
