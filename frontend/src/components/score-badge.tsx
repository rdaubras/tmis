import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/** A 0..1 float rendered as a percentage badge, colored by threshold.
 * Reused for `final_score` (recherche) and `confidence` (dossier 360,
 * enjeux, faits) — same scale, same visual language. */
export function ScoreBadge({
  value,
  label,
  className,
}: {
  value: number;
  label?: string;
  className?: string;
}) {
  const percent = Math.round(value * 100);
  const variant = percent >= 66 ? "success" : percent >= 33 ? "warning" : "outline";
  return (
    <Badge variant={variant} className={cn("tabular-nums", className)}>
      {label ? `${label} ` : ""}
      {percent}%
    </Badge>
  );
}
