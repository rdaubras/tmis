"use server";

import { revalidatePath } from "next/cache";

import { createCaseProfile } from "@/lib/api";

export async function createCaseProfileAction(formData: FormData): Promise<void> {
  const caseId = String(formData.get("case_id") ?? "");
  const title = String(formData.get("title") ?? "");
  if (!caseId || !title) {
    return;
  }
  await createCaseProfile(caseId, title);
  revalidatePath(`/cases/${caseId}`);
}
