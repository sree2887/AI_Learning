// @vitest-environment node
import { test, expect, vi, afterEach } from "vitest";
import { jwtVerify, SignJWT } from "jose";

vi.mock("server-only", () => ({}));

const mockCookieSet = vi.fn();
const mockCookieGet = vi.fn();
vi.mock("next/headers", () => ({
  cookies: vi.fn().mockResolvedValue({ set: mockCookieSet, get: mockCookieGet }),
}));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllEnvs();
});

async function getCreateSession() {
  const { createSession } = await import("@/lib/auth");
  return createSession;
}

async function getGetSession() {
  const { getSession } = await import("@/lib/auth");
  return getSession;
}

async function makeToken(
  payload: Record<string, unknown> = {},
  secret = "development-secret-key",
  exp = "7d"
) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
  return new SignJWT({ userId: "u1", email: "a@b.com", expiresAt, ...payload })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime(exp)
    .sign(new TextEncoder().encode(secret));
}

test("sets a cookie named auth-token", async () => {
  const createSession = await getCreateSession();
  await createSession("user-1", "user@example.com");

  expect(mockCookieSet).toHaveBeenCalledOnce();
  expect(mockCookieSet.mock.calls[0][0]).toBe("auth-token");
});

test("cookie is httpOnly with sameSite lax and path /", async () => {
  const createSession = await getCreateSession();
  await createSession("user-1", "user@example.com");

  const options = mockCookieSet.mock.calls[0][2];
  expect(options.httpOnly).toBe(true);
  expect(options.sameSite).toBe("lax");
  expect(options.path).toBe("/");
});

test("cookie is not secure outside production", async () => {
  vi.stubEnv("NODE_ENV", "development");
  const createSession = await getCreateSession();
  await createSession("user-1", "user@example.com");

  const options = mockCookieSet.mock.calls[0][2];
  expect(options.secure).toBe(false);
});

test("cookie is secure in production", async () => {
  vi.stubEnv("NODE_ENV", "production");
  const createSession = await getCreateSession();
  await createSession("user-1", "user@example.com");

  const options = mockCookieSet.mock.calls[0][2];
  expect(options.secure).toBe(true);
});

test("cookie expires approximately 7 days from now", async () => {
  const before = Date.now();
  const createSession = await getCreateSession();
  await createSession("user-1", "user@example.com");
  const after = Date.now();

  const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
  const expires: Date = mockCookieSet.mock.calls[0][2].expires;
  expect(expires.getTime()).toBeGreaterThanOrEqual(before + sevenDaysMs - 1000);
  expect(expires.getTime()).toBeLessThanOrEqual(after + sevenDaysMs + 1000);
});

test("JWT token contains userId and email", async () => {
  const createSession = await getCreateSession();
  await createSession("user-123", "test@example.com");

  const token: string = mockCookieSet.mock.calls[0][1];
  const secret = new TextEncoder().encode("development-secret-key");
  const { payload } = await jwtVerify(token, secret);

  expect(payload.userId).toBe("user-123");
  expect(payload.email).toBe("test@example.com");
});

test("JWT token is signed with HS256", async () => {
  const createSession = await getCreateSession();
  await createSession("user-1", "user@example.com");

  const token: string = mockCookieSet.mock.calls[0][1];
  const header = JSON.parse(atob(token.split(".")[0]));
  expect(header.alg).toBe("HS256");
});

test("getSession returns null when no cookie is present", async () => {
  mockCookieGet.mockReturnValue(undefined);
  const getSession = await getGetSession();
  const result = await getSession();
  expect(result).toBeNull();
});

test("getSession returns session payload for a valid token", async () => {
  const token = await makeToken({ userId: "user-123", email: "test@example.com" });
  mockCookieGet.mockReturnValue({ value: token });
  const getSession = await getGetSession();
  const result = await getSession();
  expect(result?.userId).toBe("user-123");
  expect(result?.email).toBe("test@example.com");
});

test("getSession payload has userId, email, and expiresAt", async () => {
  const token = await makeToken();
  mockCookieGet.mockReturnValue({ value: token });
  const getSession = await getGetSession();
  const result = await getSession();
  expect(result).toHaveProperty("userId");
  expect(result).toHaveProperty("email");
  expect(result).toHaveProperty("expiresAt");
});

test("getSession returns null for a malformed token", async () => {
  mockCookieGet.mockReturnValue({ value: "not.a.token" });
  const getSession = await getGetSession();
  const result = await getSession();
  expect(result).toBeNull();
});

test("getSession returns null when token is signed with wrong secret", async () => {
  const token = await makeToken({}, "wrong-secret");
  mockCookieGet.mockReturnValue({ value: token });
  const getSession = await getGetSession();
  const result = await getSession();
  expect(result).toBeNull();
});

test("getSession returns null for an expired token", async () => {
  const token = await makeToken({}, "development-secret-key", "0s");
  mockCookieGet.mockReturnValue({ value: token });
  const getSession = await getGetSession();
  const result = await getSession();
  expect(result).toBeNull();
});
