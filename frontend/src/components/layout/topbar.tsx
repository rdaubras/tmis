import { ThemeToggle } from "@/components/theme-toggle";

export function Topbar() {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border px-6">
      <p className="text-sm text-muted-foreground">Cabinet de démonstration</p>
      <ThemeToggle />
    </header>
  );
}
