import Link from "next/link";
import { Folder } from "lucide-react";

import { listCases } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";

import { createCaseAction } from "./actions";

export default async function CasesPage() {
  const cases = await listCases();

  return (
    <div className="flex flex-col gap-6">
      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Nouveau dossier</CardTitle>
          <CardDescription>Cycle de vie du dossier : parties, phases, statuts.</CardDescription>
        </CardHeader>
        <CardContent>
          <form action={createCaseAction} className="flex gap-3">
            <input
              name="title"
              required
              placeholder="Titre du dossier"
              className="h-10 flex-1 rounded-md border border-input bg-background px-3 text-sm"
            />
            <Button type="submit">Créer</Button>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-3">
        {cases.length === 0 ? (
          <EmptyState
            icon={Folder}
            title="Aucun dossier pour le moment"
            description="Créez votre premier dossier pour commencer à travailler."
          />
        ) : (
          cases.map((c) => (
            <Link key={c.id} href={`/cases/${c.id}`}>
              <Card className="transition-colors hover:bg-accent/50">
                <CardHeader>
                  <CardTitle className="text-base">{c.title}</CardTitle>
                  <CardDescription>Statut : {c.status}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
