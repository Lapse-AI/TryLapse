import { useState } from "react";
import { Check, ChevronDown, FlaskConical, LogOut, UserRound } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Chip } from "@/components/ui-bits";
import {
  getTestGroup,
  resolveGroupConfigId,
  TEST_GROUPS,
  type TestGroupId,
} from "@/lib/test-groups";
import { useTestGroup } from "@/hooks/use-test-group";
import { useConfigs } from "@/lib/api/hooks";
import { toast } from "sonner";

type AuthMode = "sign-in" | "sign-up";

/**
 * Product / test-group switcher — no sign-in required.
 * Sign-in is optional (localStorage) for labeling who ran a rehearsal.
 */
export function TestGroupAuth() {
  const { data: configs = [] } = useConfigs();
  const { user, isSignedIn, group, groupId, resolvedConfigId, signIn, signUp, signOut, setGroup } =
    useTestGroup();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [mode, setMode] = useState<AuthMode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const switchGroup = (id: TestGroupId) => {
    const next = getTestGroup(id);
    const configId = resolveGroupConfigId(next, configs);
    setGroup(id);
    toast.success(`Product: ${next.label}`, {
      description: `Runs & config scoped · ${configId}`,
    });
  };

  const submitAuth = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error("Email required");
      return;
    }
    if (mode === "sign-up") {
      signUp(displayName, email, password);
      toast.success("Signed up (optional — for your label only)");
    } else {
      signIn(email, password);
      toast.success("Signed in");
    }
    setDialogOpen(false);
    setPassword("");
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            aria-label={`Product: ${group.label}`}
            className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md border border-violet/35 bg-violet/8 hover:bg-violet/12 text-xs max-w-[220px]"
          >
            <FlaskConical className="size-3.5 text-violet shrink-0" />
            <span className="truncate text-foreground">{group.label}</span>
            <ChevronDown className="size-3 opacity-60 shrink-0" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-72">
          <DropdownMenuLabel className="flex flex-col gap-1">
            <span className="text-[11px] font-normal text-muted-foreground">
              Product scope · no login required
            </span>
            {isSignedIn ? (
              <span className="flex items-center gap-1.5 font-normal">
                <UserRound className="size-3.5" />
                {user?.displayName}
                <span className="text-muted-foreground font-mono text-[10px] truncate">
                  {user?.email}
                </span>
              </span>
            ) : (
              <span className="text-[11px] font-normal text-muted-foreground">
                Dashboard, runs, and compare filter to the product below.
              </span>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {TEST_GROUPS.map((g) => (
            <DropdownMenuItem
              key={g.id}
              onSelect={() => switchGroup(g.id)}
              className="flex items-start gap-2 py-2"
            >
              <Check
                className={`size-3.5 mt-0.5 shrink-0 ${g.id === groupId ? "opacity-100" : "opacity-0"}`}
              />
              <div className="min-w-0">
                <div className="text-sm">{g.label}</div>
                <div className="text-[11px] text-muted-foreground">{g.personaLabel}</div>
                <div className="text-[10px] font-mono text-muted-foreground truncate mt-0.5">
                  {g.targetUrl}
                </div>
              </div>
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <div className="px-2 py-1.5 text-[10px] text-muted-foreground font-mono">
            config · {resolvedConfigId}
          </div>
          {isSignedIn ? (
            <DropdownMenuItem onSelect={() => signOut()} className="text-muted-foreground">
              <LogOut className="size-3.5 mr-2" />
              Sign out
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem onSelect={() => setDialogOpen(true)}>
              <UserRound className="size-3.5 mr-2" />
              Sign in (optional)
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Chip tone="violet">
        <span className="hidden lg:inline">{group.personaLabel}</span>
        <span className="lg:hidden">{group.label}</span>
      </Chip>

      <AuthDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        mode={mode}
        onModeChange={setMode}
        email={email}
        password={password}
        displayName={displayName}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onDisplayNameChange={setDisplayName}
        onSubmit={submitAuth}
      />
    </>
  );
}

function AuthDialog({
  open,
  onOpenChange,
  mode,
  onModeChange,
  email,
  password,
  displayName,
  onEmailChange,
  onPasswordChange,
  onDisplayNameChange,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: AuthMode;
  onModeChange: (mode: AuthMode) => void;
  email: string;
  password: string;
  displayName: string;
  onEmailChange: (v: string) => void;
  onPasswordChange: (v: string) => void;
  onDisplayNameChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-display">Optional sign-in</DialogTitle>
          <DialogDescription>
            Not required to use the dashboard. Sign in only to label who is rehearsing (stored in
            localStorage). Switch products from the dropdown anytime.
          </DialogDescription>
        </DialogHeader>
        <div className="flex gap-2 text-xs mb-2">
          <button
            type="button"
            onClick={() => onModeChange("sign-in")}
            className={`px-2 py-1 rounded ${mode === "sign-in" ? "bg-primary/15 text-primary" : "text-muted-foreground"}`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => onModeChange("sign-up")}
            className={`px-2 py-1 rounded ${mode === "sign-up" ? "bg-primary/15 text-primary" : "text-muted-foreground"}`}
          >
            Sign up
          </button>
        </div>
        <form onSubmit={onSubmit} className="space-y-3">
          {mode === "sign-up" && (
            <div>
              <label htmlFor="tg-display-name" className="text-xs text-muted-foreground">
                Display name
              </label>
              <input
                id="tg-display-name"
                className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
                value={displayName}
                onChange={(e) => onDisplayNameChange(e.target.value)}
                placeholder="Cal.com QA"
              />
            </div>
          )}
          <div>
            <label htmlFor="tg-email" className="text-xs text-muted-foreground">
              Email
            </label>
            <input
              id="tg-email"
              type="email"
              autoComplete="email"
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
              value={email}
              onChange={(e) => onEmailChange(e.target.value)}
              placeholder="you@company.com"
            />
          </div>
          <div>
            <label htmlFor="tg-password" className="text-xs text-muted-foreground">
              Password (any value)
            </label>
            <input
              id="tg-password"
              type="password"
              autoComplete={mode === "sign-up" ? "new-password" : "current-password"}
              className="mt-1 w-full bg-surface border border-border rounded-md px-3 py-2 text-sm"
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            className="w-full text-sm px-4 py-2 rounded-md bg-primary text-primary-foreground font-medium"
          >
            {mode === "sign-in" ? "Sign in" : "Sign up"}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
