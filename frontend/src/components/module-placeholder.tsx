import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ModulePlaceholder({
  title,
  description,
  sprint,
}: {
  title: string;
  description: string;
  sprint: number;
}) {
  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Ce module est prévu au Sprint {sprint} de la roadmap (voir{" "}
          <code className="rounded bg-muted px-1 py-0.5">
            docs/09-roadmap-30-sprints.md
          </code>
          ).
        </p>
      </CardContent>
    </Card>
  );
}
