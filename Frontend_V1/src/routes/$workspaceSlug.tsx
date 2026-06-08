import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { getWorkspace } from "@/lib/workspace";

export const Route = createFileRoute("/$workspaceSlug")({
  beforeLoad: ({ params }) => {
    if (typeof window === "undefined") return;
    const ws = getWorkspace();
    if (!ws) throw redirect({ to: "/onboarding" });
    // If someone navigates to a different workspace slug, redirect to their own
    if (ws.slug !== params.workspaceSlug) {
      throw redirect({
        to: "/$workspaceSlug/dashboard",
        params: { workspaceSlug: ws.slug },
      });
    }
  },
  component: () => <Outlet />,
});
