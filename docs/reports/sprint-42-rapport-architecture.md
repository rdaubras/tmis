# Rapport d'architecture — Sprint 42 (`AgentInput.case_id` : `uuid.UUID` → `str`)

## Résumé

Le Sprint 42 corrige la dette identifiée à l'audit du Sprint 41
(docs/168-architecture-exposition-orchestrator.md, Question Ouverte n°2) :
le compromis de « parsing tolérant » (un `case_id` non-UUID devient
silencieusement `None`) rendait `SynthesisAgent` systématiquement
inopérant pour tout `case_id` réaliste, puisque `CaseStorePort` (Sprint
19) accepte des identifiants libres choisis par le client
(`"case-1"`, jamais garantis au format UUID) alors qu'`AgentInput.case_id`
était typé `uuid.UUID | None`.

**Un seul type change** : `tmis/ai/schemas/agent.py`, `AgentInput.case_id:
uuid.UUID | None` devient `case_id: str | None`. Aucun second type
introduit (`str | uuid.UUID | None` aurait recréé l'ambiguïté corrigée).

Périmètre livré : `tmis/ai/schemas/agent.py` (le type), six agents
simplifiés (`research_agent.py`, `jurisprudence_agent.py`,
`contract_agent.py`, `analysis_agent.py`, `synthesis_agent.py`,
`watch_agent.py`), quatre routeurs API simplifiés
(`chat/routes.py`, `document/routes.py`, `watch/routes.py`,
`case_intelligence/routes.py`), un vrai changement de comportement
(`platform_sdk/agent_sdk/base.py`), 7 tests unitaires nouveaux (un par
agent des six listés, plus un pour `platform_sdk`), 21 constructions de
test existantes adaptées au nouveau contrat, 1 test d'intégration
renommé/adapté (`test_case_analysis_api.py`),
docs/170-architecture-agentinput-case-id-str.md, note de révision dans
docs/09-roadmap-30-sprints.md.

**Non touchés** : `ai_team/coordinator/engine.py` (`case_id=None`
toujours compatible), `CaseStorePort`/`CaseProfile`, la logique métier des
six agents au-delà du traitement de `case_id`.

## Décisions structurantes

### Pourquoi un document dédié (docs/170) plutôt qu'une section de plus dans docs/151

`docs/151-architecture-persistance.md` documente la persistance au sens
strict (adaptateurs `SQLAlchemy*Store`, singletons de store partagés —
Sprints 26/37). Ce sprint change un contrat de la couche agent
(`AgentInput`, consommé par les sept agents de ce dépôt et cinq points
d'exposition — quatre routeurs API plus l'AGENT SDK), pas un adaptateur de
persistance. C'est un changement plus proche, par sa nature transverse,
de docs/169 (consolidation d'un composition root partagé entre agents)
que de docs/151 — un document dédié, numéroté dans la même série que les
documents par agent (162/163/164) et d'exposition (165-169), est donc
plus fidèle à la nature du changement. Même raisonnement de principe que
la décision du Sprint 37 de mettre à jour docs/151 plutôt que d'en créer
un nouveau — appliqué ici dans l'autre sens, parce que la nature du
changement diffère.

### Pourquoi `str | None` et pas `str | uuid.UUID | None`

Élargir le type en union aurait évité de toucher aux 21 tests qui
construisaient `AgentInput(case_id=uuid.UUID(...))` (voir plus bas), mais
aurait recréé exactement l'ambiguïté que ce sprint corrige : deux formes
valides pour le même champ, dont l'une (`uuid.UUID`) ne correspond à
aucune contrainte réelle côté `CaseStorePort` (qui n'exige jamais un
format UUID). La mission l'exclut explicitement (« ne pas introduire un
second type de `case_id` ... pour garder la compatibilité ») et
l'implémentation confirme que ce n'était pas nécessaire : les 21 tests
concernés ont été adaptés (voir ci-dessous), pas contournés par un type
plus permissif.

### Les quatre routeurs API : fonction conservée vs fonction supprimée

`chat/routes.py._agent_input` construit tout l'`AgentInput` — `task_id`,
`context={"query": ...}`, pas seulement `case_id` — donc conservée, avec
son corps simplifié (retrait du `try/except uuid.UUID(...)`, `payload.
case_id` passé tel quel). `document/routes.py._parse_case_id`,
`watch/routes.py._parse_case_id` et `case_intelligence/routes.py.
_parse_case_id_for_agent` n'avaient qu'une seule responsabilité — le
`try/except` de parsing — devenue un passe-plat trivial une fois retirée :
les trois sont supprimées, leurs appelants passant directement
`case_id`/`payload.case_id` à `AgentInput`. Chacun des quatre a été relu
individuellement avant de trancher (pas de suppression aveugle) : aucun ne
portait de seconde responsabilité au-delà du parsing de `case_id`.

### `platform_sdk/agent_sdk/base.py` : documenté comme un vrai changement de comportement

Contrairement aux quatre routeurs API, `BaseAgentPlugin.invoke()`
(`case_id=uuid.UUID(str(payload["case_id"])) if payload.get("case_id")
else None`) ne rattrapait aucune exception : un `case_id` non-UUID levait
une `ValueError` non gérée, faisant échouer tout l'appel — un crash, pas
une dégradation silencieuse. Après ce sprint
(`case_id=str(payload["case_id"]) if payload.get("case_id") else None`),
`invoke()` ne lève plus jamais sur ce champ. **Ce changement est
documenté explicitement à trois endroits** plutôt que noyé dans le reste
du diff : un commentaire inline dans le code lui-même, une section dédiée
dans docs/170-architecture-agentinput-case-id-str.md, et ce rapport — avec
un test dédié
(`test_agent_plugin_invoke_no_longer_raises_on_a_non_uuid_case_id`) qui
n'existait pas avant ce sprint (aucun test ne couvrait ce chemin).

### `ai_team/coordinator/engine.py` : confirmé non touché

`case_id=None` à la ligne 135 reste compatible tel quel avec le type plus
large (`str | None` accepte `None` exactement comme `uuid.UUID | None`).
Conformément à la mission, l'absence de propagation d'un `case_id` réel à
cet endroit n'est pas corrigée par ce sprint — hors périmètre, non rouvert.

## Découverte en cours d'implémentation : 21 tests construisant `AgentInput` hors du nouveau contrat

Non anticipée par le texte de mission au-delà de sa garantie générale.
Une fois le type changé et les six agents simplifiés (retrait des
`str(agent_input.case_id)`), la suite pytest complète révèle 21 échecs —
tous dans des tests qui construisaient `AgentInput` avec un objet
`uuid.UUID` réel (`case_id=uuid.UUID(case_id)`, ou `case_id = uuid.uuid4()`
directement) plutôt qu'avec la chaîne de caractères que le nouveau
contrat attend. La cause : `CaseStorePort.get()`
(`dict[str, CaseProfile]`) et `InMemoryResearchHistory.list_for_case()`
(`e.case_id == case_id`) comparent par égalité exacte de type — un objet
`uuid.UUID` n'égale jamais sa représentation `str`, même de valeur
identique — et la conversion `str(agent_input.case_id)` que ce sprint
retire des six agents absorbait jusque-là cette différence.

**Décision : adapter les 21 constructions plutôt que réintroduire la
conversion.** Réintroduire `str(agent_input.case_id)` dans les agents
aurait contredit l'instruction explicite de la mission de la retirer, et
aurait masqué que ces tests construisaient une valeur qui ne correspond
plus au contrat déclaré (`case_id: str | None`). Chaque occurrence a été
corrigée par son remplacement direct — `case_id=uuid.UUID(x)` devient
`case_id=x` (x est déjà la chaîne UUID d'origine dans tous les cas
observés) ; `case_id = uuid.uuid4()` devient `case_id = str(uuid.uuid4())`
— sans jamais changer l'assertion elle-même :

| Fichier | Occurrences corrigées |
|---|---|
| `tests/unit/agents/test_analysis_agent.py` | 2 |
| `tests/unit/agents/test_contract_agent.py` | 1 |
| `tests/unit/agents/test_jurisprudence_agent.py` | 2 |
| `tests/unit/agents/test_research_agent.py` | 1 |
| `tests/unit/agents/test_synthesis_agent.py` | 9 |
| `tests/unit/agents/test_watch_agent.py` | 1 |
| `tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py` | 0 (nouveau test seulement) |
| `tests/integration/agents/test_research_agent_integration.py` | 1 |
| `tests/integration/agents/test_jurisprudence_agent_integration.py` | 1 |
| `tests/integration/agents/test_watch_agent_integration.py` | 1 |
| `tests/integration/agents/test_synthesis_agent_integration.py` | 1 |
| `tests/integration/agents/test_verifier_agent_integration.py` | 1 |

Certaines constructions du même type (`missing_case_id = uuid.uuid4()`
dans des tests « case introuvable », ou `AgentInput(task_id=uuid.uuid4(),
case_id=uuid.uuid4())` dans `test_orchestrator.py`) n'ont **pas** été
touchées : elles passaient déjà avant et après ce sprint, la comparaison
de type n'affectant jamais un résultat « non trouvé » (un objet `uuid.
UUID` inconnu de `CaseStorePort` produit le même `None` qu'une chaîne
inconnue) ni la f-string d'avertissement (`repr(uuid.UUID(...))` contient
déjà la représentation `str` complète en sous-chaîne). Aucune modification
inutile n'a donc été faite sur ces cas.

## Reuse ledger

| Composant | Compose | Ne reconstruit jamais |
|---|---|---|
| Six agents (`case_id = agent_input.case_id`) | Le champ `str` directement | Une seconde conversion `str(...)` devenue inutile |
| `chat/routes.py._agent_input` | `payload.case_id` (déjà `str \| None`, Sprint 32) transmis tel quel | Un `try/except uuid.UUID(...)` devenu inutile |
| `document/document/watch/case_intelligence routes.py` | `case_id`/`payload.case_id` transmis directement à `AgentInput` | Les trois fonctions `_parse_case_id*` supprimées, plus de second passe-plat |
| `platform_sdk/agent_sdk/base.py` | `str(payload["case_id"])` (déjà utilisé pour `task_id` sur la même ligne du dessus) | Un `uuid.UUID(...)` qui levait sans jamais être rattrapé |

## Vérification finale

- `pytest -q` (suite complète, depuis `backend/`) → **2233 passed, 7
  skipped** (2226 mesurés directement une fois les 21 constructions de
  test hors-contrat corrigées, avant l'ajout des 7 nouveaux tests dédiés à
  ce sprint), aucune régression.
- `ruff check src/ tests/` → All checks passed.
- `mypy src/` (`mypy --strict`) → Success: no issues found in 1899 source
  files.
- Vérification bout en bout : `test_analysis_with_a_non_uuid_case_id_now_
  populates_the_synthesis` (renommé/adapté depuis le test Sprint 41
  `test_analysis_with_a_non_uuid_case_id_still_succeeds`, qui vérifiait
  l'inverse) confirme, via le `TestClient` FastAPI, qu'un dossier
  `"case-1"` réellement créé produit désormais
  `result["synthesis"]["executive_summary"]` **non vide** — la preuve
  directe que la dette Sprint 41 est corrigée, pas déplacée.

## Rappel explicite : changement de comportement dans `platform_sdk/agent_sdk/base.py`

**Avant ce sprint** : `BaseAgentPlugin.invoke()` levait une `ValueError`
non rattrapée pour tout `payload["case_id"]` ne parsant pas comme UUID —
un crash pour tout plugin agent tiers invoqué avec un identifiant de
dossier au format `CaseStorePort` natif (`"case-1"`).
**Après ce sprint** : `invoke()` ne lève plus jamais sur ce champ ; un
`case_id` non-UUID est transmis tel quel à `AgentInput.case_id`. Testé par
`test_agent_plugin_invoke_no_longer_raises_on_a_non_uuid_case_id`.

## Frontend

Aucun écran affecté — ce sprint ne change aucune route ni aucun contrat de
réponse HTTP observable, seulement le type interne d'`AgentInput.case_id`
et le comportement d'erreur de l'AGENT SDK.
