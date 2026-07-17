import "server-only";

import { redirect } from "next/navigation";

import { getAccessToken } from "@/lib/session";

const API_BASE_URL = process.env.TMIS_API_BASE_URL ?? "http://localhost:8000";
const API_V1_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Server-only fetch wrapper (T6, docs/28-legal-drafting.md): reads the
 * access token from the httpOnly cookie and injects
 * `Authorization: Bearer <token>` on every call — the one place this
 * happens, so no page ever forgets it. A missing token or a 401 from the
 * API both redirect to `/login`; nothing downstream needs to handle
 * "not authenticated" itself.
 */
async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  if (!token) {
    redirect("/login");
  }

  const response = await fetch(`${API_BASE_URL}${API_V1_PREFIX}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    redirect("/login");
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export interface CaseResponse {
  id: string;
  firm_id: string;
  title: string;
  status: string;
}

export interface ParagraphResponse {
  id: string;
  section_key: string;
  order: number;
  text: string;
  origin: string;
}

export interface SectionResponse {
  id: string;
  key: string;
  title: string;
  order: number;
  paragraphs: ParagraphResponse[];
}

export interface DraftResponse {
  id: string;
  template_id: string;
  document_type: string;
  case_id: string | null;
  title: string;
  is_draft: boolean;
  status: string;
  sections: SectionResponse[];
  created_at: string;
  updated_at: string;
}

export interface VersionResponse {
  id: string;
  document_id: string;
  version_number: number;
  author: string;
  created_at: string;
  paragraph_count: number;
}

export async function listCases(): Promise<CaseResponse[]> {
  return apiFetch<CaseResponse[]>("/cases");
}

export async function createCase(title: string): Promise<CaseResponse> {
  return apiFetch<CaseResponse>("/cases", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function createDraft(input: {
  documentType: string;
  caseId?: string;
}): Promise<DraftResponse> {
  return apiFetch<DraftResponse>("/legal-drafting/drafts", {
    method: "POST",
    body: JSON.stringify({
      document_type: input.documentType,
      case_id: input.caseId || null,
    }),
  });
}

export async function getDraft(documentId: string): Promise<DraftResponse> {
  return apiFetch<DraftResponse>(`/legal-drafting/drafts/${documentId}`);
}

export async function listDraftVersions(documentId: string): Promise<VersionResponse[]> {
  return apiFetch<VersionResponse[]>(`/legal-drafting/drafts/${documentId}/versions`);
}
