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
9. [Roadmap des 30 sprints](./09-roadmap-30-sprints.md)
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

Pour la structure de code correspondante, voir `backend/` et `frontend/`
à la racine du dépôt. Le noyau IA vit dans `backend/src/tmis/ai/`, le
moteur documentaire dans `backend/src/tmis/document_intelligence/`, le
moteur métier des dossiers dans `backend/src/tmis/case_intelligence/`.
