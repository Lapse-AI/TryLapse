import { Link } from "@tanstack/react-router";
import { Info } from "lucide-react";
import { useApiHealth } from "@/lib/api/hooks";

/** Soft hint when API is down — mock data still loads in both dev and Vision. */
export function ApiRequiredBanner() {
  const { data: live, isLoading } = useApiHealth();
  if (isLoading || live) return null;

  return (
    <div className="border-b border-border bg-surface-2/80 px-4 py-2 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
      <Info className="size-3.5 shrink-0" />
      <span>
        API offline — showing Acme mock. For live runs:{" "}
        <code className="font-mono bg-surface px-1 rounded">
          ./rehearse serve -o launch-rehearsal/artifacts
        </code>
      </span>
      <Link to="/cli" className="font-mono underline text-primary">
        CLI setup
      </Link>
    </div>
  );
}
