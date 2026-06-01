const STORAGE_KEY = "rehearse:selectedConfigId";

export function getSelectedConfigId(fallback = "lr-self"): string {
  if (typeof window === "undefined") return fallback;
  try {
    return localStorage.getItem(STORAGE_KEY) || fallback;
  } catch {
    return fallback;
  }
}

export function setSelectedConfigId(configId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, configId);
  } catch {
    /* ignore quota / private mode */
  }
}
