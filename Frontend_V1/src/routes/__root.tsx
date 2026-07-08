import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  useRouterState,
  HeadContent,
  Scripts,
  redirect,
} from "@tanstack/react-router";
import { useEffect, useRef, type ReactNode } from "react";
import { getTestUser } from "@/lib/test-auth";
import { getWorkspace } from "@/lib/workspace";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { AppSidebar } from "../components/app-sidebar";
import { RehearseTopBar } from "../components/rehearse-top-bar";
import { ApiRequiredBanner } from "../components/api-required-banner";
import { Toaster } from "../components/ui/sonner";
import { RecordingWrapper } from "../components/recording-wrapper";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="text-xs uppercase tracking-[0.18em] text-primary mb-3">404 · not found</div>
        <h1 className="font-display text-4xl font-semibold">Page off the rehearsal map</h1>
        <p className="mt-3 text-sm text-muted-foreground">
          No journey points here. Head back to the command center.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          Command center
        </Link>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="font-display text-xl font-semibold">The dashboard tripped on something</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          A panel failed to render. Try again or head home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            Try again
          </button>
          <a href="/" className="rounded-md border border-border px-4 py-2 text-sm">
            Home
          </a>
        </div>
      </div>
    </div>
  );
}

const PUBLIC_PATHS = new Set(["/signin", "/signup", "/onboarding", "/init"]);

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  beforeLoad: ({ location }) => {
    if (typeof window === "undefined") return;
    const isPublic =
      PUBLIC_PATHS.has(location.pathname) ||
      location.pathname.startsWith("/onboarding") ||
      location.pathname.startsWith("/join/");
    if (isPublic) return;
    if (!getTestUser()) throw redirect({ to: "/signin" });
    if (location.pathname === "/") {
      const ws = getWorkspace();
      if (ws)
        throw redirect({ to: "/$workspaceSlug/dashboard", params: { workspaceSlug: ws.slug } });
      throw redirect({ to: "/onboarding" });
    }
  },
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Launch Rehearsal — Monitoring" },
      {
        name: "description",
        content:
          "Observe, analyze, and stage-test the customer-facing surface of any enterprise product before launch.",
      },
      { property: "og:title", content: "Launch Rehearsal — Monitoring" },
      {
        property: "og:description",
        content: "Observe, don't modify. Persona × journey, evidence-bound, multi-agent.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
    links: [{ rel: "stylesheet", href: appCss }],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isAuthPage =
    PUBLIC_PATHS.has(pathname) ||
    pathname.startsWith("/onboarding") ||
    pathname.startsWith("/join/");
  const recordingRef = useRef(null);

  return (
    <RecordingWrapper recordRef={recordingRef} enabled={!isAuthPage}>
      <QueryClientProvider client={queryClient}>
        {isAuthPage ? (
          <div className="min-h-screen bg-background text-foreground">
            <Outlet />
          </div>
        ) : (
          <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
            <div className="hidden md:flex h-full">
              <AppSidebar />
            </div>
            <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
              <RehearseTopBar />
              <ApiRequiredBanner />
              <main className="flex-1 min-w-0 overflow-x-hidden overflow-y-auto">
                <Outlet />
              </main>
            </div>
          </div>
        )}
        <Toaster />
      </QueryClientProvider>
    </RecordingWrapper>
  );
}
