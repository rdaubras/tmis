import Link from "next/link";
import { FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import { StatusBadge } from "@/components/status-badge";
import { getCaseProfile, getDocument, listCases, type DocumentSummary } from "@/lib/api";
import { documentStatusLabel, documentStatusTone } from "@/lib/document-status";

import { DocumentDropzone } from "./dropzone";

export default async function DocumentsPage({
  searchParams,
}: {
  searchParams: Promise<{ case_id?: string }>;
}) {
  const { case_id: caseId } = await searchParams;

  const [cases, profile] = await Promise.all([
    listCases(),
    caseId ? getCaseProfile(caseId) : Promise.resolve(null),
  ]);

  const documents = profile
    ? (await Promise.all(profile.document_ids.map((id) => getDocument(id)))).filter(
        (doc): doc is DocumentSummary => doc !== null,
      )
    : [];

  return (
    <div className="flex flex-col gap-6">
      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>
            Dépôt, OCR, versionning et classification des pièces d&apos;un dossier.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentDropzone cases={cases} defaultCaseId={caseId} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Documents d&apos;un dossier</CardTitle>
          <CardDescription>
            Sélectionnez un dossier pour consulter les documents déjà rattachés.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <form action="/documents" className="flex gap-3">
            <select
              name="case_id"
              defaultValue={caseId ?? ""}
              className="h-10 flex-1 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="">Choisir un dossier...</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
            <Button type="submit" variant="outline">
              Filtrer
            </Button>
          </form>

          {!caseId ? (
            <p className="text-sm text-muted-foreground">
              Aucun dossier sélectionné pour le moment.
            </p>
          ) : !profile ? (
            <EmptyState
              icon={FileText}
              title="Aucune fiche d'intelligence pour ce dossier"
              description="Ce dossier n'a pas encore de fiche d'intelligence — les documents uploadés y seront rattachés une fois traités."
            />
          ) : documents.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="Aucun document pour ce dossier"
              description="Les documents envoyés ci-dessus apparaîtront ici une fois traités."
            />
          ) : (
            <ul className="grid gap-3">
              {documents.map((doc) => (
                <li key={doc.document_id}>
                  <Link href={`/documents/${doc.document_id}`}>
                    <Card className="transition-colors hover:bg-accent/50">
                      <CardHeader>
                        <div className="flex items-center justify-between gap-3">
                          <CardTitle className="text-base">{doc.filename}</CardTitle>
                          <StatusBadge
                            status={doc.status}
                            labels={{
                              [doc.status]: {
                                label: documentStatusLabel(doc.status),
                                tone: documentStatusTone(doc.status),
                              },
                            }}
                          />
                        </div>
                        {doc.warnings.length > 0 ? (
                          <CardDescription>{doc.warnings.length} avertissement(s)</CardDescription>
                        ) : null}
                      </CardHeader>
                    </Card>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
