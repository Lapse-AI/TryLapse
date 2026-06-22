import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { LogOut } from "lucide-react";
import { PageHeader, Panel, SectionTitle } from "@/components/ui-bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthMe, useUpdateProfile, useWorkspace, useSaveWorkspace } from "@/lib/api/hooks";
import { signOut } from "@/lib/test-auth";
import { clearWorkspace } from "@/lib/workspace";

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
  return (
    <div>
      <PageHeader
        eyebrow="account"
        title="Settings"
        description="Profile, security, and notification preferences."
      />
      <div className="p-8 max-w-[700px] space-y-6">
        <ProfileSection />
        <PasswordSection />
        <NotificationsSection />
        <DangerZoneSection />
      </div>
    </div>
  );
}
