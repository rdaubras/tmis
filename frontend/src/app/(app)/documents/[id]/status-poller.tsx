"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { documentIsReady } from "@/lib/document-status";

/**
 * The upload pipeline is asynchronous (T4, docs/14-document-intelligence.md):
 * right after upload the document sits in `received`, moving through OCR,
 * classification, etc. before `processed`. This polls by re-fetching the
 * Server Component (`router.refresh()`) every few seconds until the
 * status is terminal — never freezes the UI on the just-uploaded,
 * not-actually-ready state.
 */
export function DocumentStatusPoller({ status }: { status: string }) {
  const router = useRouter();

  useEffect(() => {
    if (documentIsReady(status)) {
      return;
    }
    const interval = setInterval(() => router.refresh(), 3000);
    return () => clearInterval(interval);
  }, [status, router]);

  return null;
}
