import { DEFAULT_TEST_GROUP_ID, type TestGroupId } from "@/lib/test-groups";
import { setSelectedConfigId } from "@/lib/selected-config";

const USER_KEY = "rehearse:testUser";
const JWT_KEY = "rehearse:jwt";
const GROUP_KEY = "rehearse:testGroupId";

export const TEST_GROUP_CHANGED_EVENT = "rehearse:test-group-changed";
export const TEST_AUTH_CHANGED_EVENT = "rehearse:test-auth-changed";

export interface TestUser {
  email: string;
  displayName: string;
  signedInAt: string;
}

function dispatch(name: string) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(name));
}

export function getTestUser(): TestUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as TestUser;
  } catch {
    return null;
  }
}

function _storeSession(user: { email: string; name: string }, jwt: string): TestUser {
  const stored: TestUser = {
    email: user.email,
    displayName: user.name || user.email.split("@")[0],
    signedInAt: new Date().toISOString(),
  };
  localStorage.setItem(USER_KEY, JSON.stringify(stored));
  localStorage.setItem(JWT_KEY, jwt);
  dispatch(TEST_AUTH_CHANGED_EVENT);
  return stored;
}

export async function signIn(email: string, password: string): Promise<TestUser> {
  const { api } = await import("@/lib/api/client");
  const { token, user } = await api.authLogin(email.trim().toLowerCase(), password);
  return _storeSession(user, token);
}

export async function signUp(
  displayName: string,
  email: string,
  password: string,
): Promise<TestUser> {
  const { api } = await import("@/lib/api/client");
  const { token, user } = await api.authSignup(
    email.trim().toLowerCase(),
    password,
    displayName.trim(),
  );
  return _storeSession(user, token);
}

export function signOut(): void {
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(JWT_KEY);
  dispatch(TEST_AUTH_CHANGED_EVENT);
}

export function getTestGroupId(): TestGroupId {
  if (typeof window === "undefined") return DEFAULT_TEST_GROUP_ID;
  try {
    const raw = localStorage.getItem(GROUP_KEY) as TestGroupId | null;
    return raw ?? DEFAULT_TEST_GROUP_ID;
  } catch {
    return DEFAULT_TEST_GROUP_ID;
  }
}

export function setTestGroupId(id: TestGroupId, configId?: string): void {
  localStorage.setItem(GROUP_KEY, id);
  if (configId) setSelectedConfigId(configId);
  dispatch(TEST_GROUP_CHANGED_EVENT);
}
