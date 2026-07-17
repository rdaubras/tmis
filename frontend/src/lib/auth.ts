import "server-only";

const API_BASE_URL = process.env.TMIS_API_BASE_URL ?? "http://localhost:8000";
const API_V1_PREFIX = "/api/v1";

export interface LoginResult {
  accessToken: string;
}

/**
 * Calls `/api/v1/auth/login` directly — unlike every other backend call
 * in this app (see `src/lib/api.ts`), there is no token yet to attach.
 * Returns `null` on invalid credentials rather than throwing: the login
 * page treats "wrong password" as an expected outcome, not an error.
 */
export async function login(email: string, password: string): Promise<LoginResult | null> {
  const response = await fetch(`${API_BASE_URL}${API_V1_PREFIX}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  const body = (await response.json()) as { access_token: string };
  return { accessToken: body.access_token };
}
