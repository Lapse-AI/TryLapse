import { useCallback, useEffect, useState } from "react";
import { getSelectedConfigId, setSelectedConfigId } from "@/lib/selected-config";
import { TEST_GROUP_CHANGED_EVENT } from "@/lib/test-auth";

/** Keeps local config id in sync with test-group switches and localStorage. */
export function usePersistedConfigId() {
  const [configId, setConfigIdState] = useState(() => getSelectedConfigId());

  useEffect(() => {
    const sync = () => setConfigIdState(getSelectedConfigId());
    sync();
    window.addEventListener(TEST_GROUP_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(TEST_GROUP_CHANGED_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const pickConfig = useCallback((id: string) => {
    setConfigIdState(id);
    setSelectedConfigId(id);
  }, []);

  return { configId, pickConfig };
}
