import Link from "next/link";
import {
  AlertTriangle,
  Clock,
  FileText,
  Scale,
  Sparkles,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/empty-state";
import { ScoreBadge } from "@/components/score-badge";
import { StatusBadge, type StatusLabels } from "@/components/status-badge";
import {
  getCase,
  getCaseAnalysis,
  getCaseProfile,
  getCaseTimeline,
  type CaseAnalysis,
} from "@/lib/api";

import { createCaseProfileAction } from "./actions";

const CASE_STATUS_LABELS: StatusLabels = {
  open: { label: "Ouvert", tone: "outline" },
  analysis_in_progress: { label: "Analyse en cours", tone: "warning" },
  drafting_in_progress: { label: "Rédaction en cours", tone: "warning" },
  pending_validation: { label: "En attente de validation", tone: "warning" },
  closed: { label: "Clôturé", tone: "secondary" },
  archived: { label: "Archivé", tone: "secondary" },
};

const ISSUE_STATUS_LABELS: StatusLabels = {
  open: { label: "Ouvert", tone: "warning" },
  resolved: { label: "Résolu", tone: "success" },
};

export default async function CaseDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ tab?: string; analyze?: string }>;
}) {
  const { id: caseId } = await params;
  const { tab, analyze } = await searchParams;

  const [caseRecord, profile] = await Promise.all([getCase(caseId), getCaseProfile(caseId)]);

  if (!caseRecord) {
    return (
      <EmptyState
        icon={FileText}
        title="Dossier introuvable"
        description="Ce dossier n'existe pas ou n'appartient pas à votre cabinet."
        action={
          <Button asChild variant="outline" size="sm">
            <Link href="/cases">Retour aux dossiers</Link>
          </Button>
        }
      />
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{caseRecord.title}</h1>
          <StatusBadge status={caseRecord.status} labels={CASE_STATUS_LABELS} className="mt-2" />
        </div>
        <EmptyState
          icon={Sparkles}
          title="Aucune fiche d'intelligence pour ce dossier"
          description="Créez la fiche pour activer la chronologie, les faits et les enjeux extraits automatiquement des documents de ce dossier."
          action={
            <form action={createCaseProfileAction}>
              <input type="hidden" name="case_id" value={caseId} />
              <input type="hidden" name="title" value={caseRecord.title} />
              <Button type="submit" size="sm">
                Créer la fiche dossier
              </Button>
            </form>
          }
        />
      </div>
    );
  }

  const [timeline, analysis] = await Promise.all([
    getCaseTimeline(caseId),
    analyze === "1" ? getCaseAnalysis(caseId) : Promise.resolve<CaseAnalysis | null>(null),
  ]);

  const inconsistencies = analysis?.result.inconsistencies ?? [];
  const inconsistentDates = new Set(inconsistencies.map((i) => i.date));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{caseRecord.title}</h1>
        <div className="mt-2 flex items-center gap-2">
          <StatusBadge status={caseRecord.status} labels={CASE_STATUS_LABELS} />
          <span className="text-xs text-muted-foreground">
            Mis à jour le {new Date(profile.updated_at).toLocaleString("fr-FR")}
          </span>
        </div>
      </div>

      <Tabs defaultValue={tab && ["profil", "chronologie", "faits", "enjeux"].includes(tab) ? tab : analyze === "1" ? "chronologie" : "profil"}>
        <TabsList>
          <TabsTrigger value="profil">Profil</TabsTrigger>
          <TabsTrigger value="chronologie">Chronologie</TabsTrigger>
          <TabsTrigger value="faits">Faits</TabsTrigger>
          <TabsTrigger value="enjeux">Enjeux</TabsTrigger>
        </TabsList>

        <TabsContent value="profil">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Users className="h-4 w-4" />
                  Parties ({profile.actors.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {profile.actors.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Aucune partie identifiée.</p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {profile.actors.map((actor) => (
                      <li key={actor.id} className="flex items-center justify-between gap-2 text-sm">
                        <span>
                          {actor.name}
                          {actor.aliases.length > 0 ? (
                            <span className="text-muted-foreground"> ({actor.aliases.join(", ")})</span>
                          ) : null}
                        </span>
                        <Badge variant="outline">{actor.type}</Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="h-4 w-4" />
                  Documents ({profile.document_ids.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {profile.document_ids.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Aucun document rattaché.</p>
                ) : (
                  <ul className="flex flex-col gap-1">
                    {profile.document_ids.map((documentId) => (
                      <li key={documentId}>
                        <Link
                          href={`/documents/${documentId}`}
                          className="text-sm font-medium hover:underline"
                        >
                          {documentId}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="chronologie">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {timeline.length} entrée(s) consolidée(s) à partir des documents du dossier.
              </p>
              {analyze !== "1" ? (
                <Button asChild variant="outline" size="sm">
                  <Link href={`/cases/${caseId}?tab=chronologie&analyze=1`}>
                    <Sparkles className="h-4 w-4" />
                    Détecter les incohérences
                  </Link>
                </Button>
              ) : null}
            </div>

            {analyze === "1" ? (
              inconsistencies.length > 0 ? (
                <Card className="border-destructive/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base text-destructive">
                      <AlertTriangle className="h-4 w-4" />
                      {inconsistencies.length} incohérence(s) de chronologie détectée(s)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-2">
                    {inconsistencies.map((inconsistency) => (
                      <div
                        key={inconsistency.date}
                        className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm"
                      >
                        <p className="font-medium">{inconsistency.date}</p>
                        <p className="text-muted-foreground">{inconsistency.reason}</p>
                        <ul className="mt-1 list-inside list-disc text-muted-foreground">
                          {inconsistency.conflicting_descriptions.map((description, index) => (
                            <li key={index}>{description}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Aucune incohérence de chronologie détectée.
                </p>
              )
            ) : null}

            {timeline.length === 0 ? (
              <EmptyState
                icon={Clock}
                title="Aucune entrée de chronologie"
                description="La chronologie se construit automatiquement au fil du traitement des documents du dossier."
              />
            ) : (
              <ul className="flex flex-col gap-3">
                {timeline.map((entry, index) => (
                  <li
                    key={`${entry.date}-${index}`}
                    className={`flex flex-col gap-1 rounded-md border p-3 ${
                      inconsistentDates.has(entry.date)
                        ? "border-destructive/50 bg-destructive/5"
                        : "border-border"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold">{entry.date}</span>
                      <div className="flex items-center gap-2">
                        {inconsistentDates.has(entry.date) ? (
                          <Badge variant="destructive">Incohérence</Badge>
                        ) : null}
                        <ScoreBadge value={entry.confidence} />
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">{entry.description}</p>
                    {entry.document_ids.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {entry.document_ids.map((documentId) => (
                          <Link
                            key={documentId}
                            href={`/documents/${documentId}`}
                            className="text-xs text-muted-foreground hover:underline"
                          >
                            {documentId}
                          </Link>
                        ))}
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </TabsContent>

        <TabsContent value="faits">
          {profile.facts.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="Aucun fait recensé"
              description="Les faits sont extraits automatiquement des documents traités dans ce dossier."
            />
          ) : (
            <ul className="flex flex-col gap-3">
              {profile.facts.map((fact) => (
                <li key={fact.id} className="rounded-md border border-border p-3">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm">{fact.description}</p>
                    <ScoreBadge value={fact.confidence} />
                  </div>
                  {fact.dates.length > 0 ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Dates : {fact.dates.join(", ")}
                    </p>
                  ) : null}
                  <div className="mt-2 flex flex-wrap gap-2">
                    {fact.confirming_document_ids.map((documentId) => (
                      <Link key={documentId} href={`/documents/${documentId}`}>
                        <Badge variant="success">Confirme · {documentId}</Badge>
                      </Link>
                    ))}
                    {fact.contradicting_document_ids.map((documentId) => (
                      <Link key={documentId} href={`/documents/${documentId}`}>
                        <Badge variant="destructive">Contredit · {documentId}</Badge>
                      </Link>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </TabsContent>

        <TabsContent value="enjeux">
          {profile.legal_issues.length === 0 ? (
            <EmptyState
              icon={Scale}
              title="Aucun enjeu identifié"
              description="Les enjeux juridiques sont détectés à partir des faits et documents du dossier."
            />
          ) : (
            <ul className="flex flex-col gap-3">
              {profile.legal_issues.map((issue) => (
                <li
                  key={issue.id}
                  className="flex items-start justify-between gap-3 rounded-md border border-border p-3"
                >
                  <p className="text-sm">{issue.description}</p>
                  <div className="flex shrink-0 items-center gap-2">
                    <StatusBadge status={issue.status} labels={ISSUE_STATUS_LABELS} />
                    <ScoreBadge value={issue.confidence} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
