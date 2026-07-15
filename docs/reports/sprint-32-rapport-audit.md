# Rapport d'audit — Sprint 32 (Chat IA : streaming + historique par dossier)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, et confirme
qu'aucun n'a changé de forme depuis son sprint d'origine.

## Fichiers désignés par le prompt : forme confirmée, aucun écart de contenu

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.ai.kernel.kernel.TMISKernel.complete()` | Gouvernance (`guardrails.validate_input`), clé de cache `f"complete:{provider_name}:{sha256(prompt)}"`, lecture/écriture `self.cache` si `use_cache`/`self.config.use_cache`, `self.provider_registry.get(provider_name).complete(prompt)`, `Evaluator.record(EvaluationMetrics(...))`. **N'appelle jamais `AIIntelligenceFabric`** | Confirmé exact par lecture directe — voir écart structurel n°1 ci-dessous |
| `TMISKernel.__init__` | `store = memory_store or InMemoryStore()` (ligne 79) — câblage en dur confirmé, exactement comme annoncé par le prompt | Confirmé exact |
| `tmis.ai.memory.ports.MemoryStorePort` | `Protocol` à trois méthodes : `get(key) -> list[str]`, `append(key, value)`, `clear(key)` | Confirmé exact, aucune modification nécessaire |
| `tmis.ai.memory.conversation_memory.ConversationMemory` | `add_message(conversation_id, role, content)` écrit `f"{role}: {content}"` sur la clé `f"conversation:{conversation_id}"` ; `get_history(conversation_id) -> list[str]` ; `clear()` | Confirmé exact — le format `"role: content"` est la convention réutilisée par le prompt construit côté endpoint (Phase 3) |
| `tmis.ai.memory.case_memory.CaseMemory` | `add_note`/`get_notes`/`clear` sur la clé `f"case:{case_id}"`, même `MemoryStorePort` que `ConversationMemory` | Confirmé exact — non utilisé par le chat de ce sprint (voir docs/160), mais partage le même store |
| `tmis.ai.memory.in_memory_store.InMemoryStore` | `dict[str, list[str]]` process-local, défaut dev/tests | Confirmé exact |
| `tmis.ai.memory.redis_store.RedisMemoryStore` | Liste Redis par clé (`rpush`/`lrange`/`delete`), préfixe `"tmis:memory:"`, déjà écrite mais jamais câblée nulle part avant ce sprint | Confirmé exact — jusqu'ici du code mort, ce sprint est le premier à la câbler via `make_memory_store()` |
| `tmis.ai.providers.ports.ProviderPort` | `Protocol` : `provider_name`, `capabilities: ProviderCapabilities`, `async def complete(prompt, *, model=None) -> ModelResponse` | Confirmé exact |
| Les 4 adaptateurs (`openai`/`anthropic`/`mistral`/`local`) | **Aucun n'effectue le moindre appel réseau vers un SDK vendeur** — chacun est le stub déterministe Sprint 2 (docstring : « no real network call is made yet »), retournant `f"[{provider_name}:{model}] {prompt}"`. `ProviderCapabilities.supports_streaming` déjà `True` pour `openai`/`anthropic`, `False` pour `mistral`/`local`, sans qu'aucun code n'exploite ce flag avant ce sprint | Confirmé exact — écart structurel n°2 ci-dessous, qui a déterminé la conception de `complete_stream()` sur les 4 adaptateurs |
| `tmis.ai.cache.factory.make_cache()` | `_shared_redis_client()` (`@lru_cache`, un seul client Redis process-wide, probé une fois via `_redis_reachable()`), `RedisCache` si joignable sinon `InMemoryCache` — patron Sprint 28 | Confirmé exact — reproduit tel quel pour `ai.memory.factory.make_memory_store()`, voir Phase 2 |
| `tmis.api.v1.router.api_router` | Un `APIRouter` FastAPI agrégeant un sous-routeur par domaine (`case_router`, `case_intelligence_router`, `document_router`, ...), chacun avec son propre préfixe | Confirmé exact — `chat_router` (préfixe `/chat`) ajouté sur le même patron |
| `frontend/src/app/(app)/chat/page.tsx` | `ModulePlaceholder` statique (`title`, `description`, `sprint=14` — un numéro de sprint obsolète, hérité d'une révision antérieure de la roadmap) | Confirmé — remplacé par une vraie interface de chat (Phase 4) |
| Composants de chat existants éventuels | **Aucun** : `grep -r "module-placeholder"` montre que les 8 pages métier (`admin`, `billing`, `cases`, `chat`, `contracts`, `documents`, `drafting`, `research`) sont toutes de simples `ModulePlaceholder` statiques. Aucune bulle de message, aucun appel `fetch` vers l'API, nulle part dans `frontend/src` avant ce sprint | Confirmé — écart structurel n°3 ci-dessous |
| `frontend/src/components/ui/{button,card}.tsx` | Seuls primitifs de design system existants : `Button` (`cva`, variantes `default/destructive/outline/secondary/ghost/link`), `Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent`/`CardFooter`. Tokens de couleur sémantiques (`bg-primary`, `bg-muted`, `text-destructive`, `border-input`, ...) définis dans `globals.css`, compatibles clair/sombre nativement | Confirmé exact — réutilisés tels quels par la page de chat, aucune nouvelle primitive `ui/` créée |
| `tmis.case_intelligence.cases.ports.CaseStorePort` | `Protocol` **synchrone** (pas de `async def`) : `get(case_id) -> CaseProfile \| None`, `save`, `get_or_create`, `list_ids` | Confirmé exact — appelé sans `await` dans l'endpoint chat, comme dans `case_intelligence/routes.py` |

Aucun de ces fichiers n'avait un contenu différent de celui attendu — le
seul travail de Phase 0 a été de confirmer, ligne par ligne, trois écarts
entre la description du prompt et le comportement réel du code, tranchés
avant tout code plutôt que découverts en cours de route.

## Trois écarts identifiés en Phase 0, tranchés avant tout code

### 1. `TMISKernel.complete()` n'a jamais appelé `AIIntelligenceFabric`

Le prompt demande que `complete_stream()` route « via
`AIIntelligenceFabric` exactement comme `complete()` ». La lecture directe
de `TMISKernel.complete()` (`ai/kernel/kernel.py`, lignes 119-155) montre
qu'il appelle `self.guardrails.validate_input(prompt)` puis
`self.provider_registry.get(provider_name).complete(prompt)` — jamais
`AIIntelligenceFabric`. `AIIntelligenceFabric` (`tmis.ai_fabric.fabric`)
est une façade séparée, câblée dans les endpoints `ai_fabric.api.routes`
via `get_ai_intelligence_fabric()`, que les modules métier appellent —
mais que `TMISKernel` lui-même n'a jamais appelée, à aucun sprint.

**Décision** : `complete_stream()` reproduit le routage *réel* de
`complete()` (guardrails puis `provider_registry`), pas la description du
prompt. Faire l'inverse aurait fait diverger le choix de provider entre
`complete()` et `complete_stream()` sur un point qu'aucune des deux
méthodes ne fait aujourd'hui dépendre d'`AIIntelligenceFabric` — un
comportement incohérent que rien dans le prompt ne justifie. Voir
docs/160-architecture-chat-ia.md.

### 2. Aucun des 4 providers n'effectue de vrai appel SDK — le critère « supporte nativement le streaming » n'a donc pas de base à observer

Le prompt demande de distinguer, par provider, « un provider dont le SDK
ne supporte pas nativement le streaming » pour décider d'un repli
`complete()` + chunk unique. La Phase 0 confirme qu'aucun des 4
adaptateurs n'appelle de SDK vendeur du tout (`grep` sur les imports
`openai`/`anthropic`/`mistralai`/`httpx` dans `ai/providers/` : aucune
correspondance) — chacun reste le stub déterministe Sprint 2. Il n'existe
donc, dans ce dépôt, aucun flux SDK natif à observer pour trancher ce
critère à la lettre.

**Décision** : réutiliser le seul signal déjà déclaré dans le dépôt —
`ProviderCapabilities.supports_streaming`, `True` pour `openai`/
`anthropic`, `False` pour `mistral`/`local` depuis le Sprint 2, jamais
exploité par aucun code avant ce sprint. `openai`/`anthropic` découpent
le texte déterministe de `complete()` mot par mot ; `mistral`/`local`
appliquent le repli exact demandé par le prompt (`complete()` puis chunk
unique). Assumé et documenté plutôt que traité comme un vrai flux SDK :
voir docs/160 pour le détail et la conséquence pour un futur sprint qui
câblerait un vrai SDK.

### 3. Aucun composant de chat, aucun appel `fetch` vers l'API : le Sprint 32 est la première page du frontend à parler au backend

Le prompt demande de chercher « un `ModulePlaceholder`, un design system
de bulles de message déjà utilisé ailleurs dans le frontend ». La Phase 0
confirme qu'aucune bulle de message n'existe nulle part, et qu'aucune
page du frontend n'effectue le moindre appel réseau vers l'API FastAPI —
les 8 pages métier existantes (`admin`, `billing`, `cases`, `chat`,
`contracts`, `documents`, `drafting`, `research`) sont toutes de simples
`ModulePlaceholder` statiques ; `frontend/package.json` ne déclare aucune
variable d'environnement `NEXT_PUBLIC_*` ni aucun client HTTP.

**Décision** : construire l'interface de chat directement sur les deux
seuls primitifs `ui/` existants (`Card`, `Button`) et les tokens de
couleur sémantiques déjà définis dans `globals.css` (compatibles clair/
sombre sans code additionnel, vérifié manuellement), plutôt que
d'introduire une nouvelle primitive `ui/` réutilisable pour un besoin qui
n'existait pas avant ce sprint (champ de saisie texte). Consommation du
flux SSE via `fetch` + `ReadableStream` plutôt que `EventSource` : `
EventSource` ne supporte que des requêtes `GET`, incompatible avec un
corps JSON `POST`. Voir docs/160.

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. Trois écarts entre la description du prompt et le
comportement réel du code (`AIIntelligenceFabric` jamais appelée par
`complete()`, absence de tout appel SDK réel sur les 4 providers, absence
de tout précédent frontend pour un chat) ont été identifiés dès la
Phase 0, tranchés avant tout code et documentés ci-dessus ainsi que dans
le rapport d'architecture et docs/160-architecture-chat-ia.md — pas
appliqués silencieusement.

Un besoin non couvert par ce sprint, identifié en cours d'implémentation
et volontairement non construit par anticipation (conformément à
l'instruction explicite du prompt sur le garde-fou de gouvernance) : un
chat généraliste sans citation est exactement le scénario où
`HallucinationDetectionEngine`/`BiasDetectionEngine` (Sprint 15) auraient
le plus de valeur, puisqu'aucune source ne vient étayer la réponse. Voir
la section correspondante de docs/160-architecture-chat-ia.md.
