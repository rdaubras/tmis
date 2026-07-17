import "server-only";

import { cookies } from "next/headers";

/**
 * The access token lives in an httpOnly cookie set by a Server Action
 * (`login/actions.ts`) right after `/api/v1/auth/login` succeeds — never
 * in `localStorage`, never readable by client JS (see docs/28-legal-drafting.md
 * § points de vigilance: the debt this sprint explicitly avoids taking on).
 * Everything that reads or writes it runs on the server only (`server-only`
 * import above turns any accidental client-side import into a build error).
 */
const ACCESS_TOKEN_COOKIE = "tmis_access_token";

// Matches the backend's own access token lifetime
// (`Settings.access_token_expire_minutes`) — the cookie should not outlive
// the token it carries.
const ACCESS_TOKEN_MAX_AGE_SECONDS = 30 * 60;

export async function getAccessToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(ACCESS_TOKEN_COOKIE)?.value ?? null;
}

export async function setAccessToken(token: string): Promise<void> {
  const store = await cookies();
  store.set(ACCESS_TOKEN_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: ACCESS_TOKEN_MAX_AGE_SECONDS,
  });
}

export async function clearAccessToken(): Promise<void> {
  const store = await cookies();
  store.delete(ACCESS_TOKEN_COOKIE);
}
