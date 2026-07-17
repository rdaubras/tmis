"use server";

import { revalidatePath } from "next/cache";

import { createCase } from "@/lib/api";

export async function createCaseAction(formData: FormData): Promise<void> {
  const title = String(formData.get("title") ?? "").trim();
  if (!title) {
    return;
  }
  await createCase(title);
  revalidatePath("/cases");
}
