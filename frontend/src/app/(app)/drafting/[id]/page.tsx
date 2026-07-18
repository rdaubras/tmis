import Link from "next/link";
import { FileText, GitCompare, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CitationCard } from "@/components/citation-card";
import { EmptyState } from "@/components/empty-state";
import { StatusBadge, type StatusLabels } from "@/components/status-badge";
import {
  compareDraftVersions,
  getDraft,
  listDraftVersions,
  type DraftVersionDiff,
} from "@/lib/api";

import { validateDraftAction } from "./actions";
import { ExportButtons } from "./export-buttons";

const DRAFT_STATUS_LABELS: StatusLabels = {
  generated: { label: "Généré", tone: "outline" },
  under_review: { label: "En relecture", tone: "warning" },
  lawyer_approved: { label: "Approuvé", tone: "success" },
  rejected: { label: "Rejeté", tone: "destructive" },
};

const REVIEW_FINDING_LABELS: StatusLabels = {
  repetition: { label: "Répétition", tone: "warning" },
  contradiction: { label: "Contradiction", tone: "destructive" },
  incomplete_section: { label: "Section incomplète", tone: "destructive" },
  missing_reference: { label: "Référence manquante", tone: "warning" },
  unjustified_paragraph: { label: "Paragraphe non justifié", tone: "warning" },
};

export default async function DraftDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ version_a?: string; version_b?: string }>;
}) {
  const { id } = await params;
  const { version_a, version_b } = await searchParams;

  const [draft, versions] = await Promise.all([getDraft(id), listDraftVersions(id)]);

  if (!draft) {
    return (
      <EmptyState
        icon={FileText}
        title="Brouillon introuvable"
        description="Ce brouillon n'existe pas ou a été supprimé."
        action={
          <Button asChild variant="outline" size="sm">
            <Link href="/drafting">Retour à la rédaction</Link>
          </Button>
        }
      />
    );
  }

  const versionA = version_a ? Number.parseInt(version_a, 10) : null;
  const versionB = version_b ? Number.parseInt(version_b, 10) : null;
  const diff: DraftVersionDiff | null =
    versionA && versionB ? await compareDraftVersions(id, versionA, versionB) : null;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle>{draft.title}</CardTitle>
              <CardDescription>
                {draft.document_type}
                {draft.case_id ? (
                  <>
                    {" "}
                    · dossier{" "}
                    <Link href={`/cases/${draft.case_id}`} className="hover:underline">
                      {draft.case_id}
                    </Link>
                  </>
                ) : null}
              </CardDescription>
            </div>
            <StatusBadge status={draft.status} labels={DRAFT_STATUS_LABELS} />
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {draft.sections.map((section) => (
            <div key={section.id} className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {section.title}
              </h3>
              {section.paragraphs.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">Section vide.</p>
              ) : (
                section.paragraphs.map((paragraph) => (
                  <p key={paragraph.id} className="text-sm leading-relaxed">
                    {paragraph.text}
                  </p>
                ))
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Actions</CardTitle>
          <CardDescription>Valider, relire, exporter ce brouillon.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <form action={validateDraftAction} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <input type="hidden" name="document_id" value={draft.id} />
            <div className="flex flex-col gap-1.5">
              <label htmlFor="decision" className="text-sm font-medium">
                Décision
              </label>
              <select
                id="decision"
                name="decision"
                required
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="approved">Approuver</option>
                <option value="rejected">Rejeter</option>
                <option value="commented">Commenter</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="author" className="text-sm font-medium">
                Votre nom
              </label>
              <input
                id="author"
                name="author"
                required
                defaultValue="avocat"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              />
            </div>
            <div className="flex flex-1 flex-col gap-1.5">
              <label htmlFor="comment" className="text-sm font-medium">
                Commentaire (facultatif)
              </label>
              <input
                id="comment"
                name="comment"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              />
            </div>
            <Button type="submit">Enregistrer la décision</Button>
          </form>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Exporter</span>
            <ExportButtons documentId={draft.id} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldAlert className="h-4 w-4" />
            Relecture
          </CardTitle>
          <CardDescription>Points signalés par le moteur de relecture.</CardDescription>
        </CardHeader>
        <CardContent>
          {draft.review_findings.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucun point de relecture signalé.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {draft.review_findings.map((finding) => (
                <li key={finding.id} className="flex items-start gap-2 rounded-md border border-border p-3">
                  <StatusBadge status={finding.type} labels={REVIEW_FINDING_LABELS} />
                  <p className="text-sm">{finding.description}</p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {draft.citations.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Citations du brouillon</CardTitle>
            <CardDescription>Sources documentaires utilisées pour générer ce texte.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {draft.citations.map((citation) => (
              <CitationCard
                key={citation.id}
                citation={{
                  reference: citation.reference,
                  excerpt: citation.excerpt,
                  documentType: citation.source_type,
                }}
              />
            ))}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Versions</CardTitle>
          <CardDescription>Historique des versions de ce brouillon.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune version enregistrée.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {versions.map((version) => (
                <li key={version.id} className="text-sm">
                  Version {version.version_number} — {version.paragraph_count} paragraphes —{" "}
                  {version.author} —{" "}
                  <span className="text-muted-foreground">
                    {new Date(version.created_at).toLocaleString("fr-FR")}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {versions.length >= 2 ? (
            <form className="flex flex-wrap items-end gap-3 border-t border-border pt-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="version_a" className="text-sm font-medium">
                  Version A
                </label>
                <select
                  id="version_a"
                  name="version_a"
                  defaultValue={version_a ?? ""}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">—</option>
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      Version {v.version_number}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="version_b" className="text-sm font-medium">
                  Version B
                </label>
                <select
                  id="version_b"
                  name="version_b"
                  defaultValue={version_b ?? ""}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">—</option>
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      Version {v.version_number}
                    </option>
                  ))}
                </select>
              </div>
              <Button type="submit" variant="outline">
                <GitCompare className="h-4 w-4" />
                Comparer
              </Button>
            </form>
          ) : null}

          {diff ? (
            <div className="grid gap-3 border-t border-border pt-4 sm:grid-cols-3">
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Ajoutés ({diff.added_paragraph_ids.length})
                </p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {diff.added_paragraph_ids.map((pid) => (
                    <Badge key={pid} variant="success">
                      {pid}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Supprimés ({diff.removed_paragraph_ids.length})
                </p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {diff.removed_paragraph_ids.map((pid) => (
                    <Badge key={pid} variant="destructive">
                      {pid}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Modifiés ({diff.changed_paragraph_ids.length})
                </p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {diff.changed_paragraph_ids.map((pid) => (
                    <Badge key={pid} variant="warning">
                      {pid}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
