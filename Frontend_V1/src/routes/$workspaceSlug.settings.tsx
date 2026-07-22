import { useEffect, useState } from "react";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { toast } from "sonner";
import { LogOut, UserPlus, X, Copy, Eye, EyeOff } from "lucide-react";
import { PageHeader, Panel, SectionTitle, Chip } from "@/components/ui-bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api/client";
import {
  useAuthMe,
  useUpdateProfile,
  useWorkspace,
  useSaveWorkspace,
  useWorkspaceMembers,
  useWorkspaceInvites,
  useInviteToWorkspace,
  useRemoveWorkspaceMember,
  useWorkspaceUsage,
  useCreateCheckoutSession,
  useMyWorkspaces,
  useCaseStudy,
} from "@/lib/api/hooks";
import { signOut } from "@/lib/test-auth";
import { clearWorkspace, getWorkspace } from "@/lib/workspace";

export const Route = createFileRoute("/$workspaceSlug/settings")({
  head: () => ({ meta: [{ title: "Settings — Launch Rehearsal" }] }),
  component: SettingsPage,
});

function ProfileSection() {
  const { data: me, isLoading } = useAuthMe();
  const updateProfile = useUpdateProfile();
  const [name, setName] = useState("");

  useEffect(() => {
    if (me?.name) setName(me.name);
  }, [me?.name]);

  const dirty = me ? name.trim() !== me.name && name.trim().length > 0 : false;

  async function saveName() {
    try {
      await updateProfile.mutateAsync({ name: name.trim() });
      toast.success("Profile updated");
    } catch {
      toast.error("Failed to update profile");
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="account" title="Profile" />
      <div className="grid gap-4 max-w-sm">
        <div className="space-y-1.5">
          <Label htmlFor="profile-email">Email</Label>
          <Input
            id="profile-email"
            value={me?.email ?? ""}
            disabled
            placeholder={isLoading ? "Loading…" : ""}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="profile-name">Name</Label>
          <Input
            id="profile-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
          />
        </div>
        <Button
          onClick={saveName}
          disabled={!dirty || updateProfile.isPending}
          size="sm"
          className="w-fit"
        >
          {updateProfile.isPending ? "Saving…" : "Save name"}
        </Button>
      </div>
    </Panel>
  );
}

function PasswordSection() {
  const updateProfile = useUpdateProfile();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");

  const canSubmit = current.length > 0 && next.length >= 8 && next === confirm;

  async function changePassword() {
    try {
      await updateProfile.mutateAsync({ currentPassword: current, newPassword: next });
      toast.success("Password updated");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch {
      toast.error("Failed to update password — check your current password");
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="security" title="Password" />
      <div className="grid gap-4 max-w-sm">
        <div className="space-y-1.5">
          <Label htmlFor="pw-current">Current password</Label>
          <Input
            id="pw-current"
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pw-next">New password</Label>
          <Input
            id="pw-next"
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            placeholder="At least 8 characters"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pw-confirm">Confirm new password</Label>
          <Input
            id="pw-confirm"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
          {next.length > 0 && confirm.length > 0 && next !== confirm && (
            <div className="text-xs text-danger">Passwords don't match</div>
          )}
        </div>
        <Button
          onClick={changePassword}
          disabled={!canSubmit || updateProfile.isPending}
          size="sm"
          className="w-fit"
        >
          {updateProfile.isPending ? "Updating…" : "Update password"}
        </Button>
      </div>
    </Panel>
  );
}

function TeamSection({ workspaceSlug }: { workspaceSlug: string }) {
  const { data: me } = useAuthMe();
  const { data: members = [], isLoading: membersLoading } = useWorkspaceMembers(workspaceSlug);
  const { data: invites = [] } = useWorkspaceInvites(workspaceSlug);
  const invite = useInviteToWorkspace(workspaceSlug);
  const removeMember = useRemoveWorkspaceMember(workspaceSlug);

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"owner" | "member" | "viewer">("member");

  const myMembership = members.find((m) => m.userId === me?.id);
  const isOwner = myMembership?.role === "owner";

  async function sendInvite() {
    const trimmed = email.trim();
    if (!trimmed) return;
    try {
      const result = await invite.mutateAsync({ email: trimmed, role });
      const link = `${window.location.origin}/join/${result.token}`;
      await navigator.clipboard.writeText(link).catch(() => {});
      toast.success(`Invite link copied — share it with ${trimmed}`);
      setEmail("");
    } catch {
      toast.error("Failed to create invite");
    }
  }

  async function copyInviteLink(token: string) {
    const link = `${window.location.origin}/join/${token}`;
    await navigator.clipboard.writeText(link).catch(() => {});
    toast.success("Invite link copied");
  }

  async function handleRemove(userId: string) {
    try {
      await removeMember.mutateAsync(userId);
      toast.success("Removed from workspace");
    } catch {
      toast.error("Failed to remove member");
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="team" title="Members" />
      <div className="space-y-2">
        {membersLoading && <div className="text-sm text-muted-foreground">Loading…</div>}
        {members.map((m) => (
          <div
            key={m.userId}
            className="flex items-center justify-between px-3 py-2 rounded-md border border-border bg-surface-2/40"
          >
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">
                {m.name}
                {m.userId === me?.id && (
                  <span className="text-xs text-muted-foreground"> (you)</span>
                )}
              </div>
              <div className="text-xs text-muted-foreground truncate">{m.email}</div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Chip tone={m.role === "owner" ? "violet" : "neutral"}>{m.role}</Chip>
              {isOwner && m.userId !== me?.id && (
                <button
                  type="button"
                  onClick={() => handleRemove(m.userId)}
                  disabled={removeMember.isPending}
                  className="text-muted-foreground hover:text-danger"
                  title="Remove from workspace"
                >
                  <X className="size-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {isOwner && invites.length > 0 && (
        <div className="space-y-2 pt-2">
          <div className="text-xs text-muted-foreground font-medium">Pending invites</div>
          {invites.map((inv) => (
            <div
              key={inv.token}
              className="flex items-center justify-between px-3 py-2 rounded-md border border-dashed border-border"
            >
              <div className="text-sm text-muted-foreground">
                {inv.email} <span className="text-xs">· {inv.role}</span>
              </div>
              <button
                type="button"
                onClick={() => copyInviteLink(inv.token)}
                className="text-muted-foreground hover:text-foreground"
                title="Copy invite link"
              >
                <Copy className="size-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {isOwner ? (
        <div className="flex items-end gap-2 pt-2 max-w-md">
          <div className="space-y-1.5 flex-1">
            <Label htmlFor="invite-email">Invite a teammate</Label>
            <Input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teammate@company.com"
            />
          </div>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as "owner" | "member" | "viewer")}
            className="h-9 rounded-md border border-border bg-background px-2 text-sm"
          >
            <option value="member">Member</option>
            <option value="viewer">Viewer (read-only)</option>
            <option value="owner">Owner</option>
          </select>
          <Button
            onClick={sendInvite}
            disabled={!email.trim() || invite.isPending}
            size="sm"
            className="gap-1.5"
          >
            <UserPlus className="size-4" />
            Invite
          </Button>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          Only the workspace owner can invite or remove teammates.
        </p>
      )}
    </Panel>
  );
}

const PLAN_LABELS: Record<string, string> = {
  design_partner: "Design Partner (90-day trial)",
  starter: "Starter — $299/mo",
  growth: "Growth — $799/mo",
  scale: "Scale — custom",
};

const PLAN_LIMITS: Record<string, number | null> = {
  design_partner: null,
  starter: 8,
  growth: 30,
  scale: null,
};

function PlanSection({ workspaceSlug }: { workspaceSlug: string }) {
  const { data: workspaces } = useMyWorkspaces();
  const { data: usage } = useWorkspaceUsage(workspaceSlug);
  const checkout = useCreateCheckoutSession();

  const current = workspaces?.find((w) => w.slug === workspaceSlug);
  const plan = current?.plan ?? "design_partner";
  const limit = PLAN_LIMITS[plan] ?? null;
  const used = usage?.runsThisMonth ?? 0;
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;

  async function upgrade(targetPlan: "starter" | "growth") {
    const result = await checkout.mutateAsync({ plan: targetPlan, workspaceSlug });
    if ("url" in result && result.url) {
      window.location.href = result.url;
    } else if ("error" in result) {
      toast.error(result.error || "Checkout is not available yet");
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="billing" title="Plan & usage" />
      <div className="flex items-center justify-between max-w-md">
        <div>
          <div className="text-sm font-medium">{PLAN_LABELS[plan] ?? plan}</div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {limit == null
              ? `${used} run${used === 1 ? "" : "s"} this month — unlimited`
              : `${used} / ${limit} runs this month`}
          </div>
        </div>
        <Chip tone={limit != null && used >= limit ? "danger" : "neutral"}>{plan}</Chip>
      </div>
      {limit != null && (
        <div className="h-1.5 rounded-full bg-surface-2 max-w-md overflow-hidden">
          <div
            className={`h-full rounded-full ${pct >= 100 ? "bg-danger" : "bg-primary"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
      {plan !== "growth" && plan !== "scale" && (
        <div className="flex gap-2">
          <Button
            onClick={() => upgrade("starter")}
            disabled={checkout.isPending || plan === "starter"}
            size="sm"
            variant="outline"
          >
            {plan === "starter" ? "Current: Starter" : "Upgrade to Starter — $299/mo"}
          </Button>
          <Button onClick={() => upgrade("growth")} disabled={checkout.isPending} size="sm">
            Upgrade to Growth — $799/mo
          </Button>
        </div>
      )}
      <p className="text-xs text-muted-foreground">
        Need unlimited runs and CI/CD gate integration? Scale is sales-assisted —{" "}
        <a href="mailto:hello@trylapse.com" className="text-primary underline">
          contact us
        </a>
        .
      </p>
    </Panel>
  );
}

function GuardrailsSection() {
  const { data: workspace } = useWorkspace();
  const saveWorkspace = useSaveWorkspace();
  const [keywords, setKeywords] = useState("");

  useEffect(() => {
    setKeywords((workspace?.guardrails?.extraBlockedKeywords ?? []).join(", "));
  }, [workspace?.guardrails?.extraBlockedKeywords]);

  async function save() {
    const list = keywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
    try {
      await saveWorkspace.mutateAsync({
        ...workspace,
        guardrails: { extraBlockedKeywords: list },
      });
      toast.success("Guardrails saved");
    } catch {
      toast.error("Failed to save guardrails");
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="safety" title="Guardrails" />
      <p className="text-sm text-muted-foreground -mt-2">
        The agent already skips obviously destructive actions (delete, cancel, unsubscribe, logout,
        etc.) during discovery. Add product-specific terms here if there's anything else it should
        never click — these are <span className="font-medium">opt-in only</span>, not applied
        automatically, since many products' real journeys legitimately test checkout or account
        changes.
      </p>
      <div className="space-y-1.5 max-w-md">
        <Label htmlFor="guardrail-keywords">Extra blocked keywords (comma-separated)</Label>
        <Input
          id="guardrail-keywords"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="downgrade plan, terminate account, place order"
        />
      </div>
      <Button onClick={save} disabled={saveWorkspace.isPending} size="sm" className="w-fit">
        {saveWorkspace.isPending ? "Saving…" : "Save guardrails"}
      </Button>
    </Panel>
  );
}

function TestCredentialsSection() {
  const userWorkspace = getWorkspace();
  const configId = userWorkspace?.configPath
    ?.split("/")
    .pop()
    ?.replace(/\.yaml$/, "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginPath, setLoginPath] = useState("/login");
  const [showPw, setShowPw] = useState(false);
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!email && !password) return;
    setSaving(true);
    try {
      const result = await api.saveCredentials(email, password, {
        configId,
        loginPath: loginPath.trim() || undefined,
      });
      toast.success(
        result.yamlUpdated
          ? "Credentials saved + auth block added to config"
          : "Credentials saved — used on next run",
      );
    } catch {
      toast.error("Failed to save credentials");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="auth" title="Test login credentials" />
      <p className="text-sm text-muted-foreground -mt-2">
        Used by the runner to log in as a test user before rehearsing authenticated journeys, for{" "}
        <span className="font-mono text-xs">{configId ?? "this workspace's"}</span> config. Stored
        in <code className="font-mono">.env</code>, never written into the config YAML.
      </p>
      <div className="grid gap-4 max-w-sm">
        <div className="space-y-1.5">
          <Label htmlFor="cred-email">Email / username</Label>
          <Input
            id="cred-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="cred-password">Password</Label>
          <div className="relative">
            <Input
              id="cred-password"
              type={showPw ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="pr-9"
            />
            <button
              type="button"
              onClick={() => setShowPw(!showPw)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
            >
              {showPw ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
            </button>
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="cred-login-path">Login page path</Label>
          <Input
            id="cred-login-path"
            value={loginPath}
            onChange={(e) => setLoginPath(e.target.value)}
            placeholder="/login"
            className="font-mono"
          />
        </div>
        <Button
          onClick={save}
          disabled={saving || (!email && !password)}
          size="sm"
          className="w-fit"
        >
          {saving ? "Saving…" : "Save credentials"}
        </Button>
      </div>
    </Panel>
  );
}

function NotificationsSection() {
  const { data: workspace } = useWorkspace();
  const saveWorkspace = useSaveWorkspace();
  const [slackUrl, setSlackUrl] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");

  useEffect(() => {
    setSlackUrl(workspace?.slackWebhookUrl ?? "");
    setWebhookUrl(workspace?.webhookUrl ?? "");
  }, [workspace?.slackWebhookUrl, workspace?.webhookUrl]);

  async function save() {
    try {
      await saveWorkspace.mutateAsync({
        ...workspace,
        slackWebhookUrl: slackUrl.trim() || null,
        webhookUrl: webhookUrl.trim() || null,
      });
      toast.success("Notification settings saved");
    } catch {
      toast.error("Failed to save notification settings");
    }
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="alerts" title="Notifications" />
      <p className="text-sm text-muted-foreground -mt-2">
        Fired on run completion — gate result posts to Slack, and the full summary POSTs as JSON to
        your webhook. Toggle which alerts are active on the{" "}
        <a href="../alerts" className="text-primary underline">
          Alerts
        </a>{" "}
        page.
      </p>
      <div className="grid gap-4 max-w-md">
        <div className="space-y-1.5">
          <Label htmlFor="slack-url">Slack incoming webhook URL</Label>
          <Input
            id="slack-url"
            value={slackUrl}
            onChange={(e) => setSlackUrl(e.target.value)}
            placeholder="https://hooks.slack.com/services/…"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="webhook-url">Generic webhook URL</Label>
          <Input
            id="webhook-url"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            placeholder="https://your-service.com/hooks/launch-rehearsal"
          />
        </div>
        <Button onClick={save} disabled={saveWorkspace.isPending} size="sm" className="w-fit">
          {saveWorkspace.isPending ? "Saving…" : "Save notification settings"}
        </Button>
      </div>
    </Panel>
  );
}

function CaseStudySection({ workspaceSlug }: { workspaceSlug: string }) {
  const { data: caseStudy, isError } = useCaseStudy(workspaceSlug);

  async function copyMarkdown() {
    if (!caseStudy) return;
    const delta = caseStudy.readinessDelta;
    const deltaStr = delta > 0 ? `+${delta}` : String(delta);
    const lines = [
      `# ${caseStudy.productName ?? "This product"} — Launch Readiness, Before & After`,
      "",
      `Across ${caseStudy.totalRuns} rehearsals, readiness moved from ${caseStudy.before.readiness} (${caseStudy.before.launchGate}) to ${caseStudy.after.readiness} (${caseStudy.after.launchGate}) — a ${deltaStr} point change.`,
      caseStudy.blockersResolved > 0 ? `${caseStudy.blockersResolved} blocker(s) resolved.` : "",
      caseStudy.outcome?.notes ? `Outcome: ${caseStudy.outcome.notes}` : "",
    ].filter(Boolean);
    await navigator.clipboard.writeText(lines.join("\n")).catch(() => {});
    toast.success("Case study copied");
  }

  return (
    <Panel className="p-6 space-y-4">
      <SectionTitle eyebrow="share" title="Case study" />
      {isError || !caseStudy ? (
        <p className="text-sm text-muted-foreground">
          Need at least 2 rehearsals to generate a before/after comparison — run a few more and
          check back.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 max-w-md text-sm">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Before</div>
              <div className="font-medium">
                {caseStudy.before.readiness} · {caseStudy.before.launchGate}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">After</div>
              <div className="font-medium">
                {caseStudy.after.readiness} · {caseStudy.after.launchGate}
              </div>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            {caseStudy.blockersResolved > 0 &&
              `${caseStudy.blockersResolved} blocker${caseStudy.blockersResolved !== 1 ? "s" : ""} resolved. `}
            {caseStudy.outcome
              ? caseStudy.outcome.launchSucceeded
                ? "Launch succeeded."
                : "Launch did not go as planned."
              : "Launch outcome not yet recorded."}
          </p>
          <Button onClick={copyMarkdown} size="sm" variant="outline" className="w-fit">
            Copy as markdown
          </Button>
        </>
      )}
    </Panel>
  );
}

function DangerZoneSection() {
  function handleSignOut() {
    signOut();
    clearWorkspace();
    window.location.href = "/signin";
  }

  return (
    <Panel className="p-6 space-y-4 border-danger/30 bg-danger/5">
      <SectionTitle eyebrow="account" title="Sign out" />
      <p className="text-sm text-muted-foreground">Sign out of Launch Rehearsal on this device.</p>
      <Button onClick={handleSignOut} variant="outline" size="sm" className="w-fit gap-2">
        <LogOut className="size-4" />
        Sign out
      </Button>
    </Panel>
  );
}

function SettingsPage() {
  const { workspaceSlug } = useParams({ from: "/$workspaceSlug/settings" });
  return (
    <div>
      <PageHeader
        eyebrow="account"
        title="Settings"
        description="Profile, security, team, and notification preferences."
      />
      <div className="p-8 max-w-[700px] space-y-6">
        <ProfileSection />
        <PasswordSection />
        <PlanSection workspaceSlug={workspaceSlug} />
        <TeamSection workspaceSlug={workspaceSlug} />
        <TestCredentialsSection />
        <GuardrailsSection />
        <NotificationsSection />
        <CaseStudySection workspaceSlug={workspaceSlug} />
        <DangerZoneSection />
      </div>
    </div>
  );
}
