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
 *
 * The three functions below (`apiFetch`, `apiFetchMultipart`,
 * `apiFetchBinary`, ADR-FE-02) all funnel through this one call so the
 * auth handling never has to be duplicated per content type.
 */
async function authorizedRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await getAccessToken();
  if (!token) {
    redirect("/login");
  }

  const response = await fetch(`${API_BASE_URL}${API_V1_PREFIX}${path}`, {
    ...init,
    headers: {
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

  return response;
}

/** JSON variant — every request/response body in this app is JSON except
 * the two cases below (upload, export). */
async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await authorizedRequest(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/**
 * Multipart variant (ADR-FE-02): the caller builds a `FormData` (file +
 * fields) and `Content-Type` is deliberately left unset so the runtime
 * fills in `multipart/form-data; boundary=...` itself — setting it by
 * hand breaks the boundary and the backend can no longer parse the body.
 */
async function apiFetchMultipart<T>(path: string, formData: FormData): Promise<T> {
  const response = await authorizedRequest(path, {
    method: "POST",
    body: formData,
  });
  return (await response.json()) as T;
}

export interface BinaryFile {
  base64: string;
  mediaType: string;
  filename: string;
}

/**
 * Binary variant (ADR-FE-02): reads the response body as bytes instead
 * of `.json()`-ing it, for endpoints that return a file (draft export).
 * Encoded as base64 so the result can cross the Server Action -> Client
 * Component boundary as a plain serializable value.
 */
async function apiFetchBinary(path: string): Promise<BinaryFile> {
  const response = await authorizedRequest(path);
  const mediaType = response.headers.get("content-type") ?? "application/octet-stream";
  const disposition = response.headers.get("content-disposition") ?? "";
  const filenameMatch = /filename="?([^"]+)"?/.exec(disposition);
  const filename = filenameMatch ? filenameMatch[1] : "export";
  const buffer = Buffer.from(await response.arrayBuffer());
  return { base64: buffer.toString("base64"), mediaType, filename };
}

// ---------------------------------------------------------------------------
// Cases (dossiers)
// ---------------------------------------------------------------------------

export interface CaseResponse {
  id: string;
  firm_id: string;
  title: string;
  status: string;
}

export async function listCases(): Promise<CaseResponse[]> {
  return apiFetch<CaseResponse[]>("/cases");
}

export async function getCase(caseId: string): Promise<CaseResponse | null> {
  try {
    return await apiFetch<CaseResponse>(`/cases/${caseId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function createCase(title: string): Promise<CaseResponse> {
  return apiFetch<CaseResponse>("/cases", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

// ---------------------------------------------------------------------------
// Recherche documentaire (legal_research) — docs/21-legal-research.md
// ---------------------------------------------------------------------------

export interface ResearchResult {
  id: string;
  title: string;
  excerpt: string;
  connector: string;
  document_type: string;
  reference: string;
  date: string | null;
  lexical_score: number;
  vector_score: number;
  authority_score: number;
  freshness_score: number;
  final_score: number;
}

export interface ResearchCitation {
  source_id: string;
  title: string;
  date: string | null;
  document_type: string;
  reference: string;
  excerpt: string;
}

export interface ResearchSearchResult {
  search_id: string;
  query: string;
  results: ResearchResult[];
  citations: ResearchCitation[];
  connectors_used: string[];
  duration_ms: number;
  cache_hit: boolean;
}

export interface ResearchHistoryEntry {
  id: string;
  query_text: string;
  timestamp: string;
  connectors_used: string[];
  duration_ms: number;
  result_count: number;
  user_id: string | null;
  case_id: string | null;
}

export async function searchResearch(input: {
  query: string;
  caseId?: string;
  connectorNames?: string[];
}): Promise<ResearchSearchResult> {
  return apiFetch<ResearchSearchResult>("/legal-research/search", {
    method: "POST",
    body: JSON.stringify({
      query: input.query,
      case_id: input.caseId || null,
      connector_names: input.connectorNames ?? null,
    }),
  });
}

export async function getResearchHistory(caseId?: string): Promise<ResearchHistoryEntry[]> {
  const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
  return apiFetch<ResearchHistoryEntry[]>(`/legal-research/history${query}`);
}

// ---------------------------------------------------------------------------
// Dossier 360 (case_intelligence) — docs/19-case-intelligence.md
// ---------------------------------------------------------------------------

export interface CaseActor {
  id: string;
  type: string;
  name: string;
  aliases: string[];
}

export interface CaseFact {
  id: string;
  description: string;
  confidence: number;
  dates: string[];
  confirming_document_ids: string[];
  contradicting_document_ids: string[];
}

export interface CaseTimelineEntry {
  date: string;
  description: string;
  document_ids: string[];
  confidence: number;
}

export interface CaseLegalIssue {
  id: string;
  description: string;
  confidence: number;
  status: string;
}

export interface CaseProfile {
  case_id: string;
  title: string;
  is_deleted: boolean;
  document_ids: string[];
  actors: CaseActor[];
  facts: CaseFact[];
  legal_issues: CaseLegalIssue[];
  updated_at: string;
}

export interface CaseAnalysisInconsistency {
  date: string;
  reason: string;
  conflicting_descriptions: string[];
}

export interface CaseAnalysisResult {
  entities: Record<string, unknown[]>;
  inconsistencies: CaseAnalysisInconsistency[];
  timeline: unknown[];
  narrative: string | null;
  model: string | null;
  synthesis: {
    executive_summary: string;
    chronological_summary: string;
    documentary_summary: string;
    case_status: string;
    open_points: string[];
  };
}

export interface CaseAnalysis {
  case_id: string;
  result: CaseAnalysisResult;
  citations: ResearchCitationLike[];
  confidence: string;
  warnings: string[];
}

export interface ResearchCitationLike {
  source_id: string;
  connector: string;
  excerpt: string;
  reference: string;
}

/**
 * A case only gets a case-intelligence profile once one is explicitly
 * created (`createCaseProfile`) — until then `GET .../profile` 404s.
 * That is a legitimate empty state ("no profile yet"), not a page error,
 * so it is translated to `null` here instead of throwing: pages decide
 * whether to render an empty state or a create-profile prompt.
 */
export async function getCaseProfile(caseId: string): Promise<CaseProfile | null> {
  try {
    return await apiFetch<CaseProfile>(`/cases/${caseId}/profile`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function createCaseProfile(caseId: string, title: string): Promise<CaseProfile> {
  return apiFetch<CaseProfile>(`/cases/${caseId}/profile`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function getCaseTimeline(caseId: string): Promise<CaseTimelineEntry[]> {
  return apiFetch<CaseTimelineEntry[]>(`/cases/${caseId}/timeline`);
}

/**
 * Runs the full analysis agent graph (entities/timeline-inconsistencies/
 * synthesis) — a computed, on-demand read (docs/168-architecture-
 * exposition-orchestrator.md), not something to call on every page load.
 * `result.inconsistencies` is the only place `TimelineInconsistency`
 * data is exposed over the API today.
 */
export async function getCaseAnalysis(caseId: string): Promise<CaseAnalysis> {
  return apiFetch<CaseAnalysis>(`/cases/${caseId}/analysis`);
}

// ---------------------------------------------------------------------------
// Éditeur de draft (legal_drafting) — docs/28-legal-drafting.md
// ---------------------------------------------------------------------------

export interface DraftParagraph {
  id: string;
  section_key: string;
  order: number;
  text: string;
  origin: string;
  fact_ids: string[];
  reference_ids: string[];
  evidence_ids: string[];
  hypothesis_ids: string[];
}

export interface DraftSection {
  id: string;
  key: string;
  title: string;
  order: number;
  paragraphs: DraftParagraph[];
  depends_on: string[];
}

export interface DraftCitation {
  id: string;
  document_id: string;
  section_id: string;
  paragraph_id: string;
  source_type: string;
  source_id: string;
  reference: string;
  excerpt: string;
}

export interface DraftReviewFinding {
  id: string;
  type: string;
  description: string;
  section_id: string | null;
  paragraph_id: string | null;
}

export interface Draft {
  id: string;
  template_id: string;
  document_type: string;
  case_id: string | null;
  title: string;
  is_draft: boolean;
  status: string;
  sections: DraftSection[];
  citations: DraftCitation[];
  review_findings: DraftReviewFinding[];
  created_at: string;
  updated_at: string;
}

export interface DraftVersion {
  id: string;
  document_id: string;
  version_number: number;
  author: string;
  created_at: string;
  paragraph_count: number;
}

export interface DraftVersionDiff {
  version_a: number;
  version_b: number;
  added_paragraph_ids: string[];
  removed_paragraph_ids: string[];
  changed_paragraph_ids: string[];
}

export interface DraftValidationRecord {
  id: string;
  document_id: string;
  decision: string;
  author: string;
  comment: string | null;
  created_at: string;
}

export async function createDraft(input: {
  documentType: string;
  caseId?: string;
}): Promise<Draft> {
  return apiFetch<Draft>("/legal-drafting/drafts", {
    method: "POST",
    body: JSON.stringify({
      document_type: input.documentType,
      case_id: input.caseId || null,
    }),
  });
}

export async function getDraft(documentId: string): Promise<Draft | null> {
  try {
    return await apiFetch<Draft>(`/legal-drafting/drafts/${documentId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function listDraftVersions(documentId: string): Promise<DraftVersion[]> {
  return apiFetch<DraftVersion[]>(`/legal-drafting/drafts/${documentId}/versions`);
}

export async function compareDraftVersions(
  documentId: string,
  versionA: number,
  versionB: number,
): Promise<DraftVersionDiff> {
  return apiFetch<DraftVersionDiff>(
    `/legal-drafting/drafts/${documentId}/versions/compare?version_a=${versionA}&version_b=${versionB}`,
  );
}

export async function validateDraft(input: {
  documentId: string;
  decision: string;
  author: string;
  comment?: string;
}): Promise<DraftValidationRecord> {
  return apiFetch<DraftValidationRecord>(`/legal-drafting/drafts/${input.documentId}/validate`, {
    method: "POST",
    body: JSON.stringify({
      decision: input.decision,
      author: input.author,
      comment: input.comment || null,
    }),
  });
}

/** Binary variant (ADR-FE-02): never `.json()` this — see `exportDraftAction`. */
export async function exportDraft(documentId: string, format: string): Promise<BinaryFile> {
  return apiFetchBinary(`/legal-drafting/drafts/${documentId}/export?format=${format}`);
}

// ---------------------------------------------------------------------------
// Documents (document_intelligence) — docs/14-document-intelligence.md
// ---------------------------------------------------------------------------

export interface DocumentUploadResult {
  document_id: string;
  task_id: string;
  status: string;
}

export interface DocumentVersion {
  version: number;
  filename: string;
  status: string;
  previous_version_id: string | null;
}

export interface DocumentSummary {
  document_id: string;
  filename: string;
  status: string;
  ocr_text: string;
  warnings: string[];
}

export interface ClauseFinding {
  clause_id: string;
  clause_type: string;
  title: string;
  status: string;
  matched_variant_id: string | null;
  risk_notes: string | null;
  jurisprudence_refs: string[];
}

export interface DocumentAnalysis {
  document_id: string;
  result: {
    clauses: ClauseFinding[];
    version_diff: {
      added_paragraphs: string[];
      removed_paragraphs: string[];
      changed_paragraphs: { before: string; after: string }[];
    } | null;
    synthesis: string | null;
    model: string | null;
  };
  citations: ResearchCitationLike[];
  confidence: string;
  warnings: string[];
}

/** Multipart variant (ADR-FE-02): `file` is a real upload, not JSON —
 * the processing pipeline runs asynchronously (`status` starts at
 * `"received"`, not `"processed"`, see `documentIsReady`). */
export async function uploadDocument(input: {
  file: File;
  caseId?: string;
}): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.set("file", input.file);
  if (input.caseId) {
    formData.set("case_id", input.caseId);
  }
  return apiFetchMultipart<DocumentUploadResult>("/documents/upload", formData);
}

export async function getDocument(documentId: string): Promise<DocumentSummary | null> {
  try {
    return await apiFetch<DocumentSummary>(`/documents/${documentId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function listDocumentVersions(documentId: string): Promise<DocumentVersion[]> {
  return apiFetch<DocumentVersion[]>(`/documents/${documentId}/versions`);
}

/** 409s while the document hasn't finished OCR yet — callers only invoke
 * this once `documentIsReady(status)` (see `lib/document-status.ts`) is
 * true. */
export async function getDocumentAnalysis(documentId: string): Promise<DocumentAnalysis> {
  return apiFetch<DocumentAnalysis>(`/documents/${documentId}/analysis`);
}
