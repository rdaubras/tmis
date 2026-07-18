import Link from "next/link";
import { AlertTriangle, FileText, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import { StatusBadge } from "@/components/status-badge";
import {
  getDocument,
  getDocumentAnalysis,
  listDocumentVersions,
  type DocumentAnalysis,
} from "@/lib/api";
import { documentIsReady, documentStatusLabel, documentStatusTone } from "@/lib/document-status";

import { DocumentStatusPoller } from "./status-poller";

export default async function DocumentDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ analyze?: string }>;
}) {
  const { id } = await params;
  const { analyze } = await searchParams;

  const [doc, versions] = await Promise.all([getDocument(id), listDocumentVersions(id)]);

  if (!doc) {
    return (
      <EmptyState
        icon={FileText}
        title="Document introuvable"
        description="Ce document n'existe pas ou n'appartient pas à votre cabinet."
        action={
          <Button asChild variant="outline" size="sm">
            <Link href="/documents">Retour aux documents</Link>
          </Button>
        }
      />
    );
  }

  const ready = documentIsReady(doc.status);
  const analysis: DocumentAnalysis | null =
    analyze === "1" && doc.status === "processed" ? await getDocumentAnalysis(id) : null;

  return (
    <div className="flex flex-col gap-6">
      <DocumentStatusPoller status={doc.status} />

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle>{doc.filename}</CardTitle>
              <CardDescription>{doc.document_id}</CardDescription>
            </div>
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
        </CardHeader>
        <CardContent>
          {!ready ? (
            <p className="text-sm text-muted-foreground">
              Traitement en cours (OCR, classification, extraction...) — cette page se met à jour
              automatiquement.
            </p>
          ) : doc.status === "failed" ? (
            <p className="text-sm text-destructive">
              Le traitement de ce document a échoué. Consultez les avertissements ci-dessous.
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">Document traité.</p>
          )}
        </CardContent>
      </Card>

      {doc.warnings.length > 0 ? (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{doc.warnings.length} avertissement(s)</AlertTitle>
          <AlertDescription>
            <ul className="list-inside list-disc">
              {doc.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Texte extrait (OCR)</CardTitle>
        </CardHeader>
        <CardContent>
          {doc.ocr_text ? (
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">
              {doc.ocr_text}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">
              {ready ? "Aucun texte extrait." : "Le texte apparaîtra une fois l'OCR terminé."}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base">Clauses détectées</CardTitle>
              <CardDescription>Analyse contractuelle du document.</CardDescription>
            </div>
            {doc.status === "processed" && analyze !== "1" ? (
              <Button asChild variant="outline" size="sm">
                <Link href={`/documents/${id}?analyze=1`}>
                  <Sparkles className="h-4 w-4" />
                  Analyser
                </Link>
              </Button>
            ) : null}
          </div>
        </CardHeader>
        <CardContent>
          {doc.status !== "processed" ? (
            <p className="text-sm text-muted-foreground">
              L&apos;analyse des clauses est disponible une fois le document traité.
            </p>
          ) : analyze !== "1" ? (
            <p className="text-sm text-muted-foreground">
              Lancez l&apos;analyse pour détecter les clauses de ce document.
            </p>
          ) : !analysis || analysis.result.clauses.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune clause détectée.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {analysis.result.clauses.map((clause) => (
                <li key={clause.clause_id} className="rounded-md border border-border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{clause.title}</p>
                    <Badge variant="outline">{clause.status}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{clause.clause_type}</p>
                  {clause.risk_notes ? (
                    <p className="mt-1 text-sm text-destructive">{clause.risk_notes}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Versions</CardTitle>
        </CardHeader>
        <CardContent>
          {versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune version enregistrée.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {versions.map((version) => (
                <li key={version.version} className="text-sm">
                  Version {version.version} — {version.filename} —{" "}
                  <span className="text-muted-foreground">{version.status}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
