# Documentation TMIS — Sprint 1

Cette documentation constitue le livrable du Sprint 1 : vision produit,
architecture fonctionnelle et technique, DDD, stratégies transverses
(multi-agents, RAG, sécurité), plan de tests et roadmap des 30 sprints.

1. [Vision produit](./01-vision.md)
2. [Architecture fonctionnelle](./02-architecture-fonctionnelle.md)
3. [Architecture technique](./03-architecture-technique.md)
4. [Domain Driven Design](./04-domain-driven-design.md)
5. [Stratégie multi-agents](./05-strategie-multi-agents.md)
6. [Stratégie RAG](./06-strategie-rag.md)
7. [Stratégie sécurité & RGPD](./07-strategie-securite.md)
8. [Plan de tests](./08-plan-de-tests.md)
9. [Roadmap détaillée (29 sprints après révisions)](./09-roadmap-30-sprints.md)
10. [AI Kernel — architecture (Sprint 2)](./10-ai-kernel.md)
11. [Architecture LangGraph (Sprint 2)](./11-langgraph-architecture.md)
12. [Architecture RAG — implémentation (Sprint 2)](./12-rag-architecture.md)
13. [Guides d'extension (provider / agent / connecteur)](./13-guides-extension.md)
14. [Document Intelligence Engine — architecture (Sprint 3)](./14-document-intelligence.md)
15. [Guide : ajouter un nouveau parser](./15-guide-nouveau-parser.md)
16. [Guide : ajouter un nouveau moteur OCR](./16-guide-nouveau-moteur-ocr.md)
17. [Guide : ajouter un nouveau classifieur](./17-guide-nouveau-classifieur.md)
18. [Guide : le Knowledge Graph](./18-guide-knowledge-graph.md)
19. [Case Intelligence Engine — architecture (Sprint 4)](./19-case-intelligence.md)
20. [Guide : ajouter un nouveau moteur d'analyse](./20-guide-nouveau-moteur-analyse.md)
21. [Legal Research Engine — architecture (Sprint 5)](./21-legal-research.md)
22. [Guide : ajouter un nouveau connecteur au LRE](./22-guide-nouveau-connecteur.md)
23. [Guide : le Ranking Engine du LRE](./23-guide-ranking-engine.md)
24. [Guide : le système de citations du LRE](./24-guide-citation-system.md)
25. [Legal Reasoning Engine — architecture (Sprint 6)](./25-legal-reasoning.md)
26. [Guide : ajouter un nouveau moteur de raisonnement](./26-guide-nouveau-moteur-raisonnement.md)
27. [Guide : les scores de confiance du LRE²](./27-guide-scores-confiance.md)
28. [Legal Drafting Studio — architecture (Sprint 7)](./28-legal-drafting.md)
29. [Guide : créer un nouveau modèle documentaire](./29-guide-nouveau-modele-documentaire.md)
30. [Guide : le Style Engine du LDS](./30-guide-moteur-style.md)
31. [Guide : le système de versioning du LDS](./31-guide-versioning.md)
32. [Guide : les exports du LDS](./32-guide-exports.md)
33. [Legal Collaboration Engine — architecture (Sprint 8)](./33-legal-collaboration.md)
34. [Guide : les rôles (RBAC)](./34-guide-roles.md)
35. [Guide : les permissions](./35-guide-permissions.md)
36. [Guide : les workflows](./36-guide-workflows.md)
37. [Guide : les notifications](./37-guide-notifications.md)
38. [Guide : les validations](./38-guide-validations.md)
39. [Cabinet Operating System — architecture (Sprint 9)](./39-cabinet-os.md)
40. [Guide : le CRM](./40-guide-crm.md)
41. [Guide : le calendrier](./41-guide-calendrier.md)
42. [Guide : la facturation](./42-guide-facturation.md)
43. [Guide : les rapports](./43-guide-rapports.md)
44. [Guide : l'API publique](./44-guide-api-publique.md)
45. [Guide : l'administration](./45-guide-administration.md)

Pour la structure de code correspondante, voir `backend/` et `frontend/`
à la racine du dépôt. Le noyau IA vit dans `backend/src/tmis/ai/`, le
moteur documentaire dans `backend/src/tmis/document_intelligence/`, le
moteur métier des dossiers dans `backend/src/tmis/case_intelligence/`,
le moteur de recherche juridique dans `backend/src/tmis/legal_research/`,
le moteur de raisonnement juridique dans `backend/src/tmis/legal_reasoning/`,
le studio de rédaction assistée dans `backend/src/tmis/legal_drafting/`,
le moteur de collaboration (indépendant de l'IA) dans
`backend/src/tmis/collaboration/`, et le système d'exploitation du
cabinet (CRM, facturation, abonnements, tableaux de bord, API publique)
dans `backend/src/tmis/cabinet_os/`.
