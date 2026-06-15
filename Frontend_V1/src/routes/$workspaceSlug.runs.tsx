import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/$workspaceSlug/runs")({
  component: () => <Outlet />,
});
