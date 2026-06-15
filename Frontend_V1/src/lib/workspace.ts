const WORKSPACE_KEY = "rehearse:workspace";

export interface WorkspaceRecord {
  id: string;
  slug: string;
  name: string;
  ownerId: string;
  targetUrl: string;
  productName: string;
  teamRole: string;
  configPath: string;
  createdAt: string;
}

export function getWorkspace(): WorkspaceRecord | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(WORKSPACE_KEY);
    return raw ? (JSON.parse(raw) as WorkspaceRecord) : null;
  } catch {
    return null;
  }
}

export function setWorkspace(ws: WorkspaceRecord): void {
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify(ws));
}

export function clearWorkspace(): void {
  localStorage.removeItem(WORKSPACE_KEY);
}
