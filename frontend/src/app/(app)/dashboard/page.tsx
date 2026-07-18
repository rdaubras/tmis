import Link from "next/link";
import { Folder, Search as SearchIcon } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import { getResearchHistory, listCases } from "@/lib/api";
import { navItems } from "@/lib/nav-config";

const RECENT_LIMIT = 5;

// Modules surfaced this sprint (T1-T4) consume real APIs — no roadmap
// "Prévu au Sprint N" badge for those, unlike the modules still pending.
const LIVE_HREFS = new Set(["/cases", "/documents", "/research", "/drafting"]);

export default async function DashboardPage() {
  const [cases, history] = await Promise.all([listCases(), getResearchHistory()]);

  const recentCases = cases.slice(0, RECENT_LIMIT);
  const recentSearches = history.slice(0, RECENT_LIMIT);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Bienvenue sur TMIS</h1>
        <p className="text-muted-foreground">
          Themis Intelligence System — votre collaborateur juridique augmenté.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Folder className="h-4 w-4" />
              Dossiers récents
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentCases.length === 0 ? (
              <EmptyState
                title="Aucun dossier"
                description="Créez votre premier dossier pour commencer."
              />
            ) : (
              <ul className="flex flex-col divide-y divide-border">
                {recentCases.map((c) => (
                  <li key={c.id} className="py-2">
                    <Link
                      href={`/cases/${c.id}`}
                      className="flex items-center justify-between text-sm hover:underline"
                    >
                      <span className="font-medium">{c.title}</span>
                      <span className="text-xs text-muted-foreground">{c.status}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <SearchIcon className="h-4 w-4" />
              Recherches récentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentSearches.length === 0 ? (
              <EmptyState
                title="Aucune recherche"
                description="Lancez une recherche documentaire pour la retrouver ici."
              />
            ) : (
              <ul className="flex flex-col divide-y divide-border">
                {recentSearches.map((entry) => (
                  <li key={entry.id} className="py-2">
                    <Link
                      href={`/research?q=${encodeURIComponent(entry.query_text)}${
                        entry.case_id ? `&case_id=${entry.case_id}` : ""
                      }`}
                      className="flex items-center justify-between text-sm hover:underline"
                    >
                      <span className="font-medium">{entry.query_text}</span>
                      <span className="text-xs text-muted-foreground">
                        {entry.result_count} résultat(s)
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground">Accès rapides</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {navItems
            .filter((item) => item.href !== "/dashboard")
            .map((item) => {
              const Icon = item.icon;
              const isLive = LIVE_HREFS.has(item.href);
              return (
                <Link key={item.href} href={item.href}>
                  <Card className="h-full transition-colors hover:bg-accent/50">
                    <CardHeader>
                      <Icon className="mb-2 h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-base">{item.title}</CardTitle>
                      {isLive ? null : (
                        <CardDescription>Prévu au Sprint {item.sprint}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent />
                  </Card>
                </Link>
              );
            })}
        </div>
      </div>
    </div>
  );
}
