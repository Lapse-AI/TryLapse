import type { ReactNode } from "react";

type VisionOnlyProps = {
  /** Section id for docs / FEATURE_SCOPE — does not hide UI in any mode. */
  section: string;
  children: ReactNode;
};

/** Marker wrapper — children always render (dev and Vision share newest UI). */
export function VisionOnly({ children }: VisionOnlyProps) {
  return <>{children}</>;
}
