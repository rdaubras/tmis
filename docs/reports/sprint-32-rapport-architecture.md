# Rapport d'architecture — Sprint 32 (Chat IA : streaming + historique par dossier)

## Résumé

Le Sprint 32 livre un chat IA généraliste en streaming, strictement
appuyé sur `TMISKernel.complete()`/`complete_stream()` — aucun agent de
`tmis.agents`, aucun `ResearchOrchestrator`/LRE n'est branché, exactement
comme l'exige le prompt (la recherche sourcée dans le chat est le
Sprint 33). La Phase 0 de re-audit
(docs/reports/sprint-32-rapport-audit.md) a confirmé que les fichiers
désignés avaient le contenu attendu, et a identifié trois écarts entre la
description du prompt et le comportement réel du code, tranchés avant
tout code.

Périmètre livré : `ai/providers/ports.py` (`ProviderPort.complete_stream`,
Protocol étendu de façon additive), les 4 adaptateurs providers
(`complete_stream()` ajouté), `ai/kernel/kernel.py`
(`TMISKernel.complete_stream()` ajoutée, `complete()` inchangée ;
`__init__` recâblé sur `make_memory_store()`), `ai/memory/factory.py`
(nouveau), `ai/cache/factory.py` (accesseur public
`get_shared_redis_client()` ajouté), `api/v1/chat/{routes,schemas}.py`
(nouveau, endpoint SSE), `api/v1/router.py` (routeur chat enregistré),
`frontend/src/app/(app)/chat/page.tsx` (réécrit intégralement), 19 tests
backend nouveaux, 0 test existant modifié, docs/160-architecture-chat-
ia.md, note de révision dans docs/09-roadmap-30-sprints.md.

## Décisions structurantes

### `complete_stream()` route comme `complete()` route réellement, pas comme le prompt le décrit

La Phase 0 a établi par lecture directe que `TMISKernel.complete()`
n'appelle jamais `AIIntelligenceFabric` — seulement
`self.provider_registry.get(provider_name).complete(prompt)`, après
`self.guardrails.validate_input(prompt)`. `AIIntelligenceFabric` est une
façade séparée (`tmis.ai_fabric.fabric`) que les endpoints
`ai_fabric.api.routes` exposent aux modules métier, mais que
`TMISKernel` lui-même n'a jamais appelée, à aucun sprint depuis sa
création.

**Décision** : `complete_stream()` reproduit le routage réel de
`complete()` — guardrails puis `provider_registry.get(provider_name).
complete_stream(prompt, model=model)` — plutôt que la description du
prompt. L'alternative (câbler `complete_stream()` sur
`AIIntelligenceFabric` alors que `complete()` ne l'est pas) aurait fait
diverger silencieusement le choix de provider entre les deux méthodes
sur un point que rien dans le prompt ne demande de faire varier. Zéro
changement sur `complete()` elle-même — même corps de fonction, mêmes
tests Sprint 2 verts sans modification.

`complete_stream()` diffère volontairement de `complete()` sur trois
points, chacun documenté plutôt que laissé implicite (voir docs/160) :
pas de cache (`self.cache` jamais consulté — un flux partiel ne se sert
pas comme une valeur unique), pas de métriques d'évaluation (le nom du
modèle réellement utilisé n'est pas retourné par
`ProviderPort.complete_stream()`, contrairement à `ModelResponse.model`
sur la voie non-streaming — étendre la signature pour l'obtenir aurait
dépassé ce que le prompt demande), et une journalisation
`ConversationMemory` conditionnée à un nouveau paramètre optionnel
`conversation_id: uuid.UUID | None = None`, appliquée uniquement après
la fin complète de la boucle `async for` — jamais chunk par chunk,
vérifié par test
(`test_complete_stream_does_not_log_to_conversation_memory_mid_stream`).

### Le critère « streaming natif du SDK » n'a rien à observer dans ce dépôt — réutilisation du flag `ProviderCapabilities.supports_streaming` déjà déclaré

La Phase 0 a confirmé qu'aucun des 4 adaptateurs providers n'effectue le
moindre appel réseau vers un SDK vendeur — chacun reste le stub
déterministe Sprint 2 (`f"[{provider_name}:{model}] {prompt}"`). Le
prompt demande un repli `complete()` + chunk unique « pour un provider
dont le SDK ne supporte pas nativement le streaming », mais aucun des
quatre n'a de SDK à interroger sur ce point.

**Décision** : réutiliser le seul signal déjà présent dans le dépôt —
`ProviderCapabilities.supports_streaming`, `True` pour `openai`/
`anthropic`, `False` pour `mistral`/`local` depuis le Sprint 2, jamais
exploité par aucun code avant ce sprint (ni `TMISKernel`, ni la
`ProviderRegistry`, ni aucun test). `openai`/`anthropic` implémentent
`complete_stream()` en découpant mot par mot le texte déterministe déjà
produit par `complete()` (`"".join(chunks) == complete().text`, vérifié
par test) ; `mistral`/`local` implémentent exactement le repli du prompt
(`complete()` puis un seul chunk). Alternative rejetée : traiter les
quatre providers identiquement (repli seul) aurait ignoré un flag déjà
déclaré et testé (`test_registry_returns_all_four_default_providers`
existant) sans justification — un flag `supports_streaming=True` qui ne
change jamais le comportement de `complete_stream()` serait un mensonge
silencieux sur la capacité annoncée.

Conséquence assumée, documentée plutôt que masquée : ce découpage n'est
pas un flux SDK réel — il n'y en a pas dans ce dépôt à ce jour. Le jour
où un vrai SDK est câblé sur un provider (hors périmètre de ce sprint),
son `complete_stream()` devra être réécrit pour relayer le flux du SDK
plutôt que de découper un texte déjà entièrement généré.

### `ai.memory.factory.make_memory_store()` — un accesseur public ajouté à `ai.cache.factory` plutôt qu'un import d'un nom privé

Le prompt exige un seul mécanisme de connexion Redis pour tout le dépôt,
et cite `ai.cache.factory` comme le patron à reproduire. La Phase 0 a
confirmé que ce mécanisme est `ai.cache.factory._shared_redis_client()`
(`@lru_cache`, un client Redis process-wide, probé une seule fois via
`_redis_reachable()`), un nom explicitement privé (préfixe `_`).

**Décision** : plutôt que d'importer `_shared_redis_client` directement
depuis `ai.memory.factory` (franchissant la frontière de module sur un
nom privé — le style de ce dépôt réserve `# noqa: SLF001` aux accès
d'attributs d'instance en test, jamais à une dépendance de production),
`ai.cache.factory` gagne un accesseur public minimal,
`get_shared_redis_client()`, qui ne fait qu'appeler
`_shared_redis_client()`. `ai.memory.factory.make_memory_store()`
l'appelle : `RedisMemoryStore` si le client existe, sinon
`InMemoryStore`. Le partage effectif du même client est vérifié par test
(`test_memory_store_and_cache_share_the_one_redis_client` : `cache.
_client is store._client is shared_client`). Alternative rejetée :
dupliquer la logique de `_shared_redis_client()`/`_redis_reachable()`
dans `ai.memory.factory` aurait recréé un second mécanisme de connexion
et un second probe Redis — exactement ce que le prompt interdit.

`TMISKernel.__init__` : `store = memory_store or InMemoryStore()` devient
`store = memory_store or make_memory_store()`. Aucun autre changement au
constructeur ; `InMemoryStore` reste le défaut effectif dans tous les
tests existants (aucun Redis joignable dans l'environnement de
développement/test, confirmé par exécution complète de la suite sans
régression).

### L'endpoint valide `case_id` et le message *avant* de retourner la `StreamingResponse`

Une fois qu'une `StreamingResponse` a commencé à envoyer ses en-têtes
(dès que FastAPI retourne l'objet), une exception levée à l'intérieur du
générateur ne peut plus devenir un code de statut HTTP propre — la
connexion se termine simplement en erreur côté client, sans corps
JSON exploitable.

**Décision** : `stream_chat()` valide `case_id` (`CaseStorePort.get()`,
`404` si absent) et le message brut (`kernel.guardrails.
validate_input(payload.message)`, `400` si le `GuardrailViolation` est
levé) *avant* de construire et retourner la `StreamingResponse` — pas à
l'intérieur du générateur `event_stream()`. `complete_stream()`
elle-même continue d'appeler `guardrails.validate_input()` sur le prompt
composé (comportement du Kernel inchangé, cohérent avec `complete()`),
mais en pratique cette seconde validation ne peut plus échouer une fois
la première passée côté endpoint : le prompt composé contient toujours
au moins `f"user: {message}"`, jamais vide si `message` ne l'est pas.
Vérifié par test (`test_chat_stream_rejects_empty_message_with_400` :
`400` avant tout octet de flux).

### Persistance du tour : l'utilisateur par l'endpoint, l'assistant par le Kernel — jamais les deux au même endroit

`TMISKernel` ne voit jamais le message brut de l'utilisateur isolément :
il ne reçoit que le prompt composé (historique + tour courant). L'endpoint
est donc le seul endroit qui peut persister `"user: {message}"` tel
quel ; `complete_stream()` (Phase 1) est le seul endroit qui peut
persister le tour assistant une fois le flux entièrement assemblé, sans
dupliquer la boucle `async for` côté endpoint. Chacun des deux appelle
`ConversationMemory.add_message()` une fois, jamais l'un pour le compte
de l'autre — vérifié par test
(`test_chat_stream_persists_the_full_turn_scoped_per_conversation` :
exactement `["user: ...", "assistant: ..."]`, aucune duplication, aucune
fuite entre deux `conversation_id` différents).

### Frontend : `fetch` + `ReadableStream`, pas `EventSource` — et pas de nouvelle primitive `ui/`

`EventSource` ne supporte que des requêtes `GET` sans corps ; l'endpoint
attend un corps JSON `POST` (`conversation_id`, `message`, `case_id`
optionnel). `fetch` avec lecture manuelle de `response.body.getReader()`
est donc la seule option côté navigateur pour ce contrat — un parseur
minimal découpe le flux sur les séparateurs `"\n\n"` du format SSE et met
à jour le contenu du dernier message assistant à chaque chunk `data:
{"chunk": ...}` reçu.

La Phase 0 a confirmé qu'aucune bulle de message ni aucun champ de saisie
générique n'existait dans `components/ui/` avant ce sprint (seuls
`Button`/`Card`). Plutôt que d'introduire une nouvelle primitive `ui/`
pour un besoin qui n'existait nulle part ailleurs dans le dépôt (un champ
`textarea`/`input` stylé), la page de chat réutilise directement les
tokens de couleur sémantiques déjà exploités par `button.tsx`/`card.tsx`
(`border-input`, `bg-background`, `bg-primary`, `bg-muted`,
`text-destructive`, `focus-visible:ring-ring`) — compatibles clair/sombre
sans le moindre code additionnel, vérifié manuellement (bascule du thème
existant, capture d'écran en clair et en sombre). Alternative rejetée :
créer un `components/ui/textarea.tsx`/`input.tsx` générique pour un seul
site d'utilisation — une abstraction prématurée qu'aucune autre page du
dépôt ne demande aujourd'hui.

Pas de sélecteur de dossier en liste déroulante : `case_intelligence`
n'expose aucun endpoint de listing des `CaseProfile` (`GET/POST/PATCH/
DELETE /{case_id}/profile` seulement, jamais `GET /cases`), et en
ajouter un aurait dépassé le périmètre Phase 3 du prompt. Le champ est un
identifiant de dossier en texte libre, validé côté serveur par le `404`
existant — un choix delibérément minimal, documenté plutôt que présenté
comme un vrai sélecteur avec autocomplétion.

## Bug corrigé en cours d'implémentation, hors du champ initial du diff

Aucun — ce sprint n'a touché aucun code préexistant en dehors des points
listés ci-dessus (`TMISKernel.__init__`, `ai.cache.factory` pour
l'accesseur public). Aucune régression, aucun comportement préexistant
modifié.

## Test existant modifié : aucun

Les 2106 tests préexistants (Sprint 31 inclus) passent tous sans
modification — vérifié par exécution complète. 19 tests nouveaux :

- `tests/unit/ai/test_providers.py` (+3) : découpage multi-chunk et
  réassemblage exact pour `openai`/`anthropic`, repli chunk unique pour
  `mistral`/`local`, `model` respecté en streaming.
- `tests/unit/ai/test_memory_factory.py` (+5, nouveau fichier) : défaut
  `InMemoryStore` si Redis injoignable, `RedisMemoryStore` si joignable,
  partage du même client Redis que `ai.cache.factory`, jamais d'échec au
  démarrage avec la configuration réelle de l'environnement de test.
- `tests/integration/ai/test_kernel_integration.py` (+5) :
  `complete_stream()` restitue les chunks dans l'ordre, guardrails
  toujours appliqués, journalisation `ConversationMemory` uniquement
  après la fin du flux (jamais mid-stream), aucun effet de bord sans
  `conversation_id`, `complete()` toujours utilisable sur la même
  instance de Kernel.
- `tests/integration/ai/test_chat_api_integration.py` (+6, nouveau
  fichier) : plusieurs chunks SSE distincts + `event: done`, persistance
  du tour complet scopée par `conversation_id` (deux dossiers différents
  ne se contaminent jamais), `404` sur `case_id` inconnu, `200` sur
  `case_id` connu, `400` sur message vide.

Aucun test n'utilise `app.dependency_overrides` (jamais utilisé ailleurs
dans ce dépôt) : comme `tests/integration/ai/test_kernel_integration.py`
et les tests d'intégration `cabinet_knowledge`/`business_platform`
existants, le test d'API chat enregistre un provider de test directement
sur le singleton `get_kernel()` réel.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `ProviderPort.complete_stream` + 4 adaptateurs | `ProviderCapabilities.supports_streaming` (déjà déclaré, Sprint 2), `complete()` (chaque implémentation de `complete_stream` l'appelle) | Un second modèle de réponse, un second calcul de tokens |
| `TMISKernel.complete_stream()` | `self.guardrails`, `self.provider_registry`, `self.conversation_memory` — les mêmes attributs que `complete()` | `AIIntelligenceFabric` (jamais appelée par `complete()` non plus), un second mécanisme de cache/évaluation |
| `ai.memory.factory.make_memory_store()` | `ai.cache.factory.get_shared_redis_client()` (nouvel accesseur public sur le même mécanisme Sprint 28) | Un second client Redis, un second probe de joignabilité |
| `api.v1.chat.routes.stream_chat` | `get_kernel()` (singleton existant), `get_case_intelligence_workflow().case_store` (`CaseStorePort`, patron identique à `api.v1.case_intelligence.routes`), `ConversationMemory` | Un second store de conversation, une seconde validation de dossier |
| `frontend/(app)/chat/page.tsx` | `Card`/`CardContent`, `Button`, tokens de couleur `globals.css`, `cn()` | Un second primitif `ui/` pour un champ de saisie, un second design de bulle |

## Vérification finale

- `ruff check .` → All checks passed
- `mypy src` (1898 fichiers) → Success, aucune erreur
- `pytest` → 2125 tests passants (2106 préexistants + 19 nouveaux),
  7 skipped (préexistants, gatés par
  `TMIS_REDIS_URL`/`TMIS_RUN_MODEL_DOWNLOAD_TESTS`), aucune régression
- Couverture globale : 96 % (seuil CI 90 %, identique au Sprint 31) ;
  code nouveau à 100 % : `ai/providers/{ports,openai_provider,
  anthropic_provider,mistral_provider,local_provider}.py`,
  `ai/memory/factory.py`, `ai/cache/factory.py`,
  `api/v1/chat/{routes,schemas}.py` ; `ai/kernel/kernel.py` à 98 % (2
  lignes non couvertes, `get_prompt`/`run_tool` — des pass-through
  préexistants non touchés par ce sprint)
- `frontend` : `npx tsc --noEmit` → aucune erreur ; `npx eslint` → aucune
  erreur ; `npm run build` → build de production réussi, 11 routes
  générées dont `/chat`
- Vérification manuelle bout en bout (backend `uvicorn` + frontend
  `next dev` démarrés localement, pilotés via `curl -N` et Playwright/
  Chromium) : flux SSE multi-chunks réel observé sur `/api/v1/chat/
  stream` avec le provider `openai` par défaut (10 chunks distincts puis
  `event: done`, pas un seul bloc) ; historique conversationnel
  effectivement réinjecté dans le prompt d'un second tour sur la même
  `conversation_id` ; `case_id` inconnu → `404` avant tout octet de flux ;
  interface `/chat` : envoi d'un message, bulles utilisateur/assistant
  correctement positionnées et colorées en clair et en sombre (bascule du
  thème existant), curseur de streaming visible pendant la réception,
  message d'erreur affiché proprement sur un `case_id` invalide (bulle
  assistant vide retirée, pas de bulle fantôme), aucune erreur console
  dans les deux thèmes

## Confirmation explicite de périmètre

- **Aucun agent de `tmis.agents` et aucun `ResearchOrchestrator`/LRE
  n'a été branché sur le chat** — le chat de ce sprint parle uniquement
  à `TMISKernel.complete()`/`complete_stream()`, exactement le périmètre
  annoncé par la ligne 32 de la table détaillée
  (docs/09-roadmap-30-sprints.md) et confirmé distinct du Sprint 33
  (« Recherche exposée dans le chat avec citations », ligne 33).
- **`ProviderPort.complete()` et `TMISKernel.complete()` n'ont pas
  changé de signature ni de comportement** — `complete_stream()` est une
  méthode entièrement nouvelle sur les deux, jamais une modification de
  l'existant. Vérifié par test
  (`test_complete_unchanged_signature_still_works_alongside_complete_
  stream`) et par l'absence de toute modification du corps de
  `complete()` dans le diff.
- **Un seul mécanisme de connexion Redis pour tout le dépôt** :
  `ai.memory.factory.make_memory_store()` appelle le même
  `_shared_redis_client()` que `ai.cache.factory.make_cache()`, via le
  nouvel accesseur public `get_shared_redis_client()` — jamais un second
  client, jamais un second probe. Vérifié par test.
- **`InMemoryStore` reste le défaut dev/tests** — `TMISKernel.__init__`
  n'échoue jamais si Redis est absent ou injoignable ; les 2125 tests de
  la suite s'exécutent tous avec `InMemoryStore` (aucun Redis joignable
  dans l'environnement de test), vérifié par exécution.
- **Aucun garde-fou de gouvernance/hallucination construit sur le chat**,
  conformément à l'instruction explicite du prompt — `VerifierAgent`
  reste scopé au graphe `Orchestrator`. Le besoin réel identifié (un chat
  sans citation est le scénario où `HallucinationDetectionEngine`/
  `BiasDetectionEngine` auraient le plus de valeur) est signalé dans le
  rapport d'audit et docs/160, pas construit par anticipation.
