# TMIS — Themis Intelligence System

## Vision produit

TMIS n'est **pas un chatbot**. TMIS est un **AI Legal Operating System** : une
plateforme SaaS qui accompagne l'avocat sur l'intégralité du cycle de vie
d'un dossier — de l'ouverture du dossier à l'archivage, en passant par
l'analyse documentaire, la recherche juridique, la rédaction et la
collaboration au sein du cabinet.

L'avocat garde à tout moment la maîtrise de la décision. TMIS **propose** :
analyses, synthèses, recherches, brouillons, références vérifiables. Il ne
**décide** jamais à sa place et ne signe jamais un acte en son nom.

### Principes directeurs

1. **Augmenter, jamais remplacer.** Chaque fonctionnalité doit répondre à la
   question : *comment fait-on gagner du temps à un avocat tout en lui
   laissant la maîtrise de la décision ?*
2. **Transparence par construction.** Toute réponse fondée sur une recherche
   documentaire doit exposer ses sources et permettre de les consulter.
   Toute incertitude doit être signalée explicitement plutôt que masquée.
3. **Vérifiabilité.** Aucune citation, aucun texte, aucune décision de
   jurisprudence n'est avancé sans référence traçable jusqu'au document
   source (agent Vérificateur, cf. `05-strategie-multi-agents.md`).
4. **Neutralité technologique.** Le système ne dépend d'aucun fournisseur de
   modèle IA unique ; les connecteurs de données juridiques et les
   fournisseurs de modèles sont interchangeables.
5. **Sécurité et conformité par défaut.** RGPD, OWASP, chiffrement,
   auditabilité et suppression sécurisée sont des exigences non
   négociables, pas des options.

## À qui s'adresse TMIS (V1)

- Avocats indépendants ("Solo")
- Cabinets d'avocats de toute taille ("Cabinet")
- Directions juridiques et structures assimilées ("Entreprise") — accès via
  API/abonnement, sans développement dédié en V1

L'architecture est conçue pour accueillir dans le futur d'autres professions
réglementées (notaires, experts-comptables, directions juridiques
d'entreprise) **sans refonte majeure** — ces modules ne sont pas développés
en V1, mais aucun choix technique de V1 ne doit les rendre impossibles ou
coûteux à ajouter.

## Ce que TMIS fait (modules V1)

Gestion de cabinet, gestion des utilisateurs, gestion des dossiers,
documents, OCR, chat IA, recherche documentaire, analyse IA, chronologie,
contrats, rédaction assistée, tableau de bord, facturation, administration.

Voir `02-architecture-fonctionnelle.md` pour le détail de chaque module et
`09-roadmap-30-sprints.md` pour l'ordre de construction.

## Ce que TMIS ne fait pas

- TMIS ne rend pas de conseil juridique de manière autonome : toute
  production (consultation, conclusions, courrier...) est un **brouillon**
  explicitement marqué comme tel, à la relecture et validation de l'avocat.
- TMIS n'automatise pas de décision opposable à un tiers.
- TMIS ne verrouille pas le cabinet sur un unique fournisseur de modèle IA
  ou de source documentaire.

## Critères de succès

- Time-to-value : un cabinet peut créer son espace, importer des dossiers
  et obtenir une première analyse en moins de 15 minutes.
- Fiabilité perçue : 100 % des réponses reposant sur une recherche
  documentaire exposent leurs sources ; 0 citation non vérifiable livrée
  sans avertissement.
- Adoption : conçu pour equiper, à terme, plusieurs milliers de cabinets
  d'avocats en France.
