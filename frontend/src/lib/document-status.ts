/**
 * Shared with a Client Component (`documents/[id]/status-poller.tsx`), so
 * this must NOT live in `lib/api.ts` — that module is `server-only` and
 * poisons any file that imports from it, even for a pure helper like
 * this one. See `tmis.document_intelligence.schemas.document.
 * ProcessingStatus` backend-side for the full state list; everything
 * between `received` and `processed` still means "keep polling".
 */
export function documentIsReady(status: string): boolean {
  return status === "processed" || status === "failed";
}

export type DocumentStatusTone = "success" | "destructive" | "warning";

export function documentStatusTone(status: string): DocumentStatusTone {
  if (status === "processed") return "success";
  if (status === "failed") return "destructive";
  return "warning";
}

const STATUS_LABELS_FR: Record<string, string> = {
  received: "Reçu",
  processed: "Traité",
  failed: "Échec",
};

export function documentStatusLabel(status: string): string {
  return STATUS_LABELS_FR[status] ?? status.replace(/_/g, " ");
}
