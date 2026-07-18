"use client";

import { useState, useTransition } from "react";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";

import { exportDraftAction } from "./actions";

const FORMATS: { value: string; label: string }[] = [
  { value: "docx", label: "Word (.docx)" },
  { value: "pdf", label: "PDF" },
  { value: "html", label: "HTML" },
];

function base64ToBlob(base64: string, mediaType: string): Blob {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mediaType });
}

/** ADR-FE-02 binary variant: the server action returns bytes, this
 * component is the one place that turns them into a browser download —
 * never `.json()` an export response. */
export function ExportButtons({ documentId }: { documentId: string }) {
  const [pending, startTransition] = useTransition();
  const [pendingFormat, setPendingFormat] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleExport(format: string) {
    setError(null);
    setPendingFormat(format);
    startTransition(async () => {
      try {
        const file = await exportDraftAction(documentId, format);
        const blob = base64ToBlob(file.base64, file.mediaType);
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = file.filename;
        link.click();
        URL.revokeObjectURL(url);
      } catch {
        setError("Échec de l'export. Réessayez.");
      } finally {
        setPendingFormat(null);
      }
    });
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {FORMATS.map((format) => (
          <Button
            key={format.value}
            type="button"
            variant="outline"
            size="sm"
            disabled={pending}
            onClick={() => handleExport(format.value)}
          >
            <Download className="h-4 w-4" />
            {pending && pendingFormat === format.value ? "Export en cours..." : format.label}
          </Button>
        ))}
      </div>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
