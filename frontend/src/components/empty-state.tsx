import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/** T0 (surfacer les verticales) — the one "0 results" component every
 * page reuses instead of hand-rolling its own empty message. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="items-center text-center">
        {Icon ? <Icon className="mb-2 h-8 w-8 text-muted-foreground" /> : null}
        <CardTitle className="text-base">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      {action ? <CardContent className="flex justify-center pt-0">{action}</CardContent> : null}
    </Card>
  );
}
