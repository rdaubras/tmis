"use server";

import { revalidatePath } from "next/cache";

import { exportDraft, validateDraft, type BinaryFile } from "@/lib/api";

export async function validateDraftAction(formData: FormData): Promise<void> {
  const documentId = String(formData.get("document_id") ?? "");
  const decision = String(formData.get("decision") ?? "");
  const author = String(formData.get("author") ?? "").trim();
  const comment = String(formData.get("comment") ?? "").trim();
  if (!documentId || !decision || !author) {
    return;
  }
  await validateDraft({ documentId, decision, author, comment: comment || undefined });
  revalidatePath(`/drafting/${documentId}`);
}

/**
 * Binary variant (ADR-FE-02): called directly from a Client Component
 * (not via a `<form action>`) because triggering a browser download
 * needs client-side code — `apiFetch`/`exportDraft` stay server-only
 * (httpOnly cookie), so this Server Action is the bridge: it fetches the
 * file server-side and hands the bytes back as base64.
 */
export async function exportDraftAction(documentId: string, format: string): Promise<BinaryFile> {
  return exportDraft(documentId, format);
}
