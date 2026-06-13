import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { RunDetail } from "./runs.$runId";

const searchSchema = z.object({
  tab: z.string().optional(),
  step: z.string().optional(),
  dimension: z.string().optional(),
});

// Renders the full run detail in-place at /$workspaceSlug/runs/$runId so the
// URL bar retains workspace scope after navigation from the workspace run list.
// RunDetail uses useParams({ strict: false }) so it reads runId from this route.
export const Route = createFileRoute("/$workspaceSlug/runs/$runId")({
  validateSearch: searchSchema,
  head: ({ params }) => ({ meta: [{ title: `${params.runId} — Run detail` }] }),
  component: RunDetail,
  notFoundComponent: () => (
    <div className="p-12 text-center text-muted-foreground">Run not found.</div>
  ),
});
