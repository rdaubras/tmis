import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { navItems } from "@/lib/nav-config";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Bienvenue sur TMIS</h1>
        <p className="text-muted-foreground">
          Themis Intelligence System — votre collaborateur juridique augmenté.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {navItems
          .filter((item) => item.href !== "/dashboard")
          .map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href}>
                <Card className="h-full transition-colors hover:bg-accent/50">
                  <CardHeader>
                    <Icon className="mb-2 h-5 w-5 text-muted-foreground" />
                    <CardTitle className="text-base">{item.title}</CardTitle>
                    <CardDescription>Prévu au Sprint {item.sprint}</CardDescription>
                  </CardHeader>
                  <CardContent />
                </Card>
              </Link>
            );
          })}
      </div>
    </div>
  );
}
