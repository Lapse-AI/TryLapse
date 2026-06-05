import { useCallback, useEffect, useState } from "react";
import {
  getTestGroup,
  resolveGroupConfigId,
  type TestGroup,
  type TestGroupId,
} from "@/lib/test-groups";
import {
  getTestGroupId,
  getTestUser,
  setTestGroupId as persistTestGroupId,
  signIn,
  signOut,
  signUp,
  TEST_AUTH_CHANGED_EVENT,
  TEST_GROUP_CHANGED_EVENT,
  type TestUser,
} from "@/lib/test-auth";
import { setSelectedConfigId } from "@/lib/selected-config";
import { useConfigs } from "@/lib/api/hooks";

export function useTestGroup() {
  const { data: configs = [] } = useConfigs();
  const [user, setUser] = useState<TestUser | null>(() =>
    typeof window === "undefined" ? null : getTestUser(),
  );
  const [groupId, setGroupIdState] = useState<TestGroupId>(() =>
    typeof window === "undefined" ? "lr-self" : getTestGroupId(),
  );

  const sync = useCallback(() => {
    setUser(getTestUser());
    setGroupIdState(getTestGroupId());
  }, []);

  useEffect(() => {
    sync();
    window.addEventListener(TEST_AUTH_CHANGED_EVENT, sync);
    window.addEventListener(TEST_GROUP_CHANGED_EVENT, sync);
    return () => {
      window.removeEventListener(TEST_AUTH_CHANGED_EVENT, sync);
      window.removeEventListener(TEST_GROUP_CHANGED_EVENT, sync);
    };
  }, [sync]);

  const group = getTestGroup(groupId);
  const resolvedConfigId = resolveGroupConfigId(group, configs);

  useEffect(() => {
    if (!configs.length) return;
    const configId = resolveGroupConfigId(group, configs);
    setSelectedConfigId(configId);
  }, [configs, group]);

  const setGroup = useCallback(
    (id: TestGroupId) => {
      const next = getTestGroup(id);
      const configId = resolveGroupConfigId(next, configs);
      persistTestGroupId(id, configId);
      setGroupIdState(id);
    },
    [configs],
  );

  return {
    user,
    isSignedIn: Boolean(user),
    group,
    groupId,
    resolvedConfigId,
    signIn,
    signUp,
    signOut: () => {
      signOut();
      setUser(null);
    },
    setGroup,
    refreshUser: sync,
  };
}

export type TestGroupState = ReturnType<typeof useTestGroup>;

/** Display target host for workspace chrome — active test group (guest or signed in). */
export function displayTargetForGroup(group: TestGroup): string {
  return group.targetUrl.replace(/^https?:\/\//, "");
}
