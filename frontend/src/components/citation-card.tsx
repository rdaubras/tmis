import { Quote } from "lucide-react";

/** Normalized shape every citation-bearing endpoint gets mapped to
 * before rendering (`ResearchCitationResponse`, `DraftCitationResponse`,
 * the case/document analysis `CitationResponse`) — the differentiator
 * called out in the sprint doc: every result traces back to a source. */
export interface CitationCardData {
  reference: string;
  excerpt: string;
  title?: string | null;
  date?: string | null;
  documentType?: string | null;
  connector?: string | null;
}

export function CitationCard({ citation }: { citation: CitationCardData }) {
  const meta = [citation.documentType, citation.connector, citation.date].filter(Boolean);
  return (
    <div className="flex gap-3 rounded-md border border-border bg-muted/30 p-3">
      <Quote className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="flex flex-col gap-1">
        {citation.title ? <p className="text-sm font-medium">{citation.title}</p> : null}
        <p className="text-sm italic leading-relaxed text-muted-foreground">
          &laquo;&nbsp;{citation.excerpt}&nbsp;&raquo;
        </p>
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">{citation.reference}</span>
          {meta.length > 0 ? ` — ${meta.join(" · ")}` : ""}
        </p>
      </div>
    </div>
  );
}
