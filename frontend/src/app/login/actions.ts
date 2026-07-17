"use server";

import { redirect } from "next/navigation";

import { login } from "@/lib/auth";
import { setAccessToken } from "@/lib/session";

export async function loginAction(formData: FormData): Promise<void> {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");

  const result = await login(email, password);
  if (result === null) {
    redirect("/login?error=1");
  }

  await setAccessToken(result.accessToken);
  redirect("/cases");
}
