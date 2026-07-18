"use server";

import { redirect } from "next/navigation";

import { uploadDocument } from "@/lib/api";

export async function uploadDocumentAction(formData: FormData): Promise<void> {
  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return;
  }
  const caseId = String(formData.get("case_id") ?? "");

  const result = await uploadDocument({ file, caseId: caseId || undefined });
  redirect(`/documents/${result.document_id}`);
}
