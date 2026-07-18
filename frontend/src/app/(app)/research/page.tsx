import Link from "next/link";
import { History as HistoryIcon, Search as SearchIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CitationCard } from "@/components/citation-card";
import { EmptyState } from "@/components/empty-state";
import { ScoreBadge } from "@/components/score-badge";
import { getResearchHistory, listCases, searchResearch } from "@/lib/api";

export default async function ResearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; case_id?: string }>;
}) {
  const { q, case_id: rawCaseId } = await searchParams;
  const query = q?.trim();
  const caseId = rawCaseId || undefined;

  const [cases, history, searchResult] = await Promise.all([
    listCases(),
    getResearchHistory(caseId),
    query ? searchResearch({ query, caseId }) : Promise.resolve(null),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Recherche documentaire</CardTitle>
          <CardDescription>
            Recherche hybride sur les sources juridiques configurées (codes, jurisprudence,
            doctrine).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3 sm:flex-row" action="/research">
            <input
              type="text"
              name="q"
              defaultValue={q ?? ""}
              required
              placeholder="Rechercher une notion, un article, une référence..."
              className="h-10 flex-1 rounded-md border border-input bg-background px-3 text-sm"
            />
            <select
              name="case_id"
              defaultValue={rawCaseId ?? ""}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm sm:w-56"
            >
              <option value="">Tous les dossiers</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
            <Button type="submit">
              <SearchIcon className="h-4 w-4" />
              Rechercher
            </Button>
          </form>
        </CardContent>
      </Card>

      {query ? (
        searchResult && searchResult.results.length > 0 ? (
          <>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-muted-foreground">
                {searchResult.results.length} résultat(s) pour « {searchResult.query} »
              </h2>
              <p className="text-xs text-muted-foreground">
                {Math.round(searchResult.duration_ms)} ms
                {searchResult.cache_hit ? " · depuis le cache" : ""}
              </p>
            </div>

            {searchResult.connectors_used.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {searchResult.connectors_used.map((connector) => (
                  <Badge key={connector} variant="outline">
                    {connector}
                  </Badge>
                ))}
              </div>
            ) : null}

            <div className="grid gap-3">
              {searchResult.results.map((result) => (
                <Card key={result.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <CardTitle className="text-base">{result.title}</CardTitle>
                        <CardDescription>
                          {result.document_type} · {result.reference}
                          {result.date ? ` · ${result.date}` : ""} · {result.connector}
                        </CardDescription>
                      </div>
                      <ScoreBadge value={result.final_score} />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {result.excerpt}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {searchResult.citations.length > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Citations vérifiables</CardTitle>
                  <CardDescription>
                    Chaque résultat renvoie à sa source — vérifiez la référence avant de citer.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  {searchResult.citations.map((citation) => (
                    <CitationCard
                      key={citation.source_id}
                      citation={{
                        title: citation.title,
                        reference: citation.reference,
                        excerpt: citation.excerpt,
                        date: citation.date,
                        documentType: citation.document_type,
                      }}
                    />
                  ))}
                </CardContent>
              </Card>
            ) : null}
          </>
        ) : (
          <EmptyState
            icon={SearchIcon}
            title="Aucun résultat"
            description={`Aucune source ne correspond à « ${query} ». Essayez une autre formulation ou élargissez à tous les dossiers.`}
          />
        )
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <HistoryIcon className="h-4 w-4" />
            Historique des recherches
          </CardTitle>
          <CardDescription>
            {caseId ? "Recherches effectuées dans ce dossier." : "Vos recherches récentes."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune recherche pour le moment.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-border">
              {history.map((entry) => (
                <li
                  key={entry.id}
                  className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm"
                >
                  <Link
                    href={`/research?q=${encodeURIComponent(entry.query_text)}${
                      entry.case_id ? `&case_id=${entry.case_id}` : ""
                    }`}
                    className="font-medium hover:underline"
                  >
                    {entry.query_text}
                  </Link>
                  <span className="text-xs text-muted-foreground">
                    {new Date(entry.timestamp).toLocaleString("fr-FR")} · {entry.result_count}{" "}
                    résultat(s) · {Math.round(entry.duration_ms)} ms
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
