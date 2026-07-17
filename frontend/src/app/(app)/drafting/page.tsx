import { listCases } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { createDraftAction } from "./actions";

const DOCUMENT_TYPES: { value: string; label: string }[] = [
  { value: "consultation", label: "Consultation" },
  { value: "note_interne", label: "Note interne" },
  { value: "courrier", label: "Courrier" },
  { value: "mise_en_demeure", label: "Mise en demeure" },
  { value: "requete", label: "Requête" },
  { value: "assignation", label: "Assignation" },
  { value: "conclusions", label: "Conclusions" },
  { value: "memoire", label: "Mémoire" },
  { value: "synthese", label: "Synthèse" },
];

export default async function DraftingPage() {
  const cases = await listCases();

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Nouveau brouillon</CardTitle>
        <CardDescription>
          Brouillons de consultations, conclusions, courriers et notes internes.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form action={createDraftAction} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="document_type" className="text-sm font-medium">
              Type de document
            </label>
            <select
              id="document_type"
              name="document_type"
              required
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              {DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="case_id" className="text-sm font-medium">
              Dossier (facultatif)
            </label>
            <select
              id="case_id"
              name="case_id"
              defaultValue=""
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

          <Button type="submit" className="mt-2">
            Générer le brouillon
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
