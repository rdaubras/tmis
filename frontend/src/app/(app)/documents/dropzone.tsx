"use client";

import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CaseResponse } from "@/lib/api";

import { uploadDocumentAction } from "./actions";

/** Multipart variant (ADR-FE-02): a plain `<form action={serverAction}>`
 * with a file input — Next.js serializes it as `multipart/form-data`
 * automatically and hands the raw `FormData` (including the `File`) to
 * the server action, which forwards it to `lib/api.ts#uploadDocument`. */
export function DocumentDropzone({
  cases,
  defaultCaseId,
}: {
  cases: CaseResponse[];
  defaultCaseId?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) {
      return;
    }
    if (inputRef.current) {
      inputRef.current.files = files;
    }
    setFileName(files[0].name);
  }

  return (
    <form action={uploadDocumentAction} className="flex flex-col gap-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed p-8 text-center transition-colors ${
          dragging ? "border-primary bg-accent/50" : "border-input"
        }`}
      >
        <UploadCloud className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium">
          {fileName ?? "Glissez-déposez un document, ou cliquez pour parcourir"}
        </p>
        <p className="text-xs text-muted-foreground">PDF, Word, image...</p>
        <input
          ref={inputRef}
          type="file"
          name="file"
          required
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="case_id" className="text-sm font-medium">
          Dossier (facultatif)
        </label>
        <select
          id="case_id"
          name="case_id"
          defaultValue={defaultCaseId ?? ""}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">Aucun dossier</option>
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.title}
            </option>
          ))}
        </select>
      </div>

      <Button type="submit" className="w-fit">
        Envoyer le document
      </Button>
    </form>
  );
}
