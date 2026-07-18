"use client";

import { AlertTriangle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

/** T0 (surfacer les verticales): the one error boundary every route's
 * `error.tsx` renders — a clear message plus a retry, never a blank
 * screen. `apiFetch` already redirects 401s to `/login`, so whatever
 * lands here is a real failure (backend down, 5xx, network). */
export function RouteError({
  error,
  reset,
  title = "Une erreur est survenue",
}: {
  error: Error & { digest?: string };
  reset: () => void;
  title?: string;
}) {
  return (
    <Alert variant="destructive" className="max-w-xl">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <div className="flex flex-col gap-3">
          <div>
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription>
              {error.message || "Le service est temporairement indisponible."}
            </AlertDescription>
          </div>
          <Button variant="outline" size="sm" onClick={reset} className="w-fit">
            Réessayer
          </Button>
        </div>
      </div>
    </Alert>
  );
}
