import { createFileRoute, redirect } from "@tanstack/react-router";

// Redirect /$workspaceSlug/runs/$runId → /runs/$runId (existing detailed run view)
export const Route = createFileRoute("/$workspaceSlug/runs/$runId")({
  beforeLoad: ({ params }) => {
    throw redirect({ to: "/runs/$runId", params: { runId: params.runId } });
  },
  component: () => null,
});
