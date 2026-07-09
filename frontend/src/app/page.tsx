import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
      <span className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
        Themis Intelligence System
      </span>
      <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        L&apos;AI Legal Operating System des cabinets d&apos;avocats
      </h1>
      <p className="max-w-xl text-lg text-muted-foreground">
        TMIS augmente l&apos;avocat sur tout le cycle de vie d&apos;un dossier —
        sans jamais décider à sa place.
      </p>
      <Button asChild size="lg">
        <Link href="/dashboard">Accéder à l&apos;espace de démonstration</Link>
      </Button>
    </div>
  );
}
