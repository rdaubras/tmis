import { Badge, type BadgeProps } from "@/components/ui/badge";

export type StatusTone = NonNullable<BadgeProps["variant"]>;

export type StatusLabels = Record<string, { label: string; tone: StatusTone }>;

/** Generic status pill: each domain (draft workflow, document
 * processing, legal issue, clause finding, ...) supplies its own
 * `labels` map of raw backend value -> French label + tone; unknown
 * values fall back to the raw string so nothing silently disappears. */
export function StatusBadge({
  status,
  labels,
  className,
}: {
  status: string;
  labels?: StatusLabels;
  className?: string;
}) {
  const entry = labels?.[status];
  return (
    <Badge variant={entry?.tone ?? "secondary"} className={className}>
      {entry?.label ?? status}
    </Badge>
  );
}
