import { getDraft, listDraftVersions } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default async function DraftDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [draft, versions] = await Promise.all([getDraft(id), listDraftVersions(id)]);

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{draft.title}</CardTitle>
          <CardDescription>
            {draft.document_type} — statut : {draft.status}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {draft.sections.map((section) => (
            <div key={section.id} className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {section.title}
              </h3>
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph.id} className="text-sm leading-relaxed">
                  {paragraph.text}
                </p>
              ))}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Versions</CardTitle>
          <CardDescription>Historique des versions de ce brouillon.</CardDescription>
        </CardHeader>
        <CardContent>
          {versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune version enregistrée.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {versions.map((version) => (
                <li key={version.id} className="text-sm">
                  Version {version.version_number} — {version.paragraph_count} paragraphes —{" "}
                  {version.author}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
