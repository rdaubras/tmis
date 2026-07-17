"use server";

import { redirect } from "next/navigation";

import { createDraft } from "@/lib/api";

export async function createDraftAction(formData: FormData): Promise<void> {
  const documentType = String(formData.get("document_type") ?? "consultation");
  const caseId = String(formData.get("case_id") ?? "");

  const draft = await createDraft({
    documentType,
    caseId: caseId.length > 0 ? caseId : undefined,
  });

  redirect(`/drafting/${draft.id}`);
}
