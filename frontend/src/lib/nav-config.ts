import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Folder,
  FileText,
  Search,
  FileSignature,
  PenLine,
  MessagesSquare,
  Receipt,
  ShieldCheck,
} from "lucide-react";

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  /** Sprint from docs/09-roadmap-30-sprints.md that delivers this module. */
  sprint: number;
}

export const navItems: NavItem[] = [
  { title: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard, sprint: 22 },
  { title: "Dossiers", href: "/cases", icon: Folder, sprint: 4 },
  { title: "Documents", href: "/documents", icon: FileText, sprint: 5 },
  { title: "Recherche documentaire", href: "/research", icon: Search, sprint: 8 },
  { title: "Contrats", href: "/contracts", icon: FileSignature, sprint: 17 },
  { title: "Rédaction", href: "/drafting", icon: PenLine, sprint: 18 },
  { title: "Chat IA", href: "/chat", icon: MessagesSquare, sprint: 14 },
  { title: "Facturation", href: "/billing", icon: Receipt, sprint: 3 },
  { title: "Administration", href: "/admin", icon: ShieldCheck, sprint: 23 },
];
