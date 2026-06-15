// Root index — auth guard in __root.tsx handles the redirect to
// /:workspaceSlug/dashboard or /onboarding before this ever renders.
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: () => null,
});
