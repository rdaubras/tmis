"use client";

import { RouteError } from "@/components/route-error";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteError error={error} reset={reset} title="Impossible de charger le tableau de bord" />;
}
