# 170 — Architecture : `AgentInput.case_id` passe de `uuid.UUID | None` à `str | None` (Sprint 42)

Ce document décrit la correction de la dette identifiée à l'audit du
Sprint 41 (`docs/reports/sprint-41-rapport-audit.md`,
docs/168-architecture-exposition-orchestrator.md, Question Ouverte n°2) :
le compromis de « parsing tolérant » qu'appliquaient `document/routes.py`,
`chat/routes.py`, `watch/routes.py` et `case_intelligence/routes.py`
(`uuid.UUID(case_id)` si possible, `None` sinon) rendait `SynthesisAgent`
systématiquement inopérant pour tout `case_id` réaliste, puisque
`CaseStorePort` (Sprint 19) accepte des identifiants libres choisis par le
client (`"case-1"`, jamais garantis au format UUID) alors qu'`AgentInput.
case_id` était typé `uuid.UUID | None`. Voir le rapport d'audit
(`docs/reports/sprint-42-rapport-audit.md`) pour le détail composant par
composant et le rapport d'architecture
(`docs/reports/sprint-42-rapport-architecture.md`) pour le récit complet
des décisions.

## Le changement

Un seul type change, dans `tmis/ai/schemas/agent.py` :

```python
@dataclass
class AgentInput:
    task_id: uuid.UUID
    case_id: str | None          # était: uuid.UUID | None
    context: dict[str, object] = field(default_factory=dict)
```

Aucun second type n'est introduit (pas de `str | uuid.UUID | None`) : ça
recréerait exactement l'ambiguïté que ce sprint corrige. Un `case_id` qui
se trouve être un UUID (le cas de la plupart des tests existants,
`str(uuid.uuid4())`) reste une chaîne de caractères parfaitement valide —
aucune perte d'information, aucune conversion nécessaire pour ce cas.

## Pourquoi ce changement est mécanique et sûr

`CaseStorePort.get(case_id: str)` (Sprint 19,
`case_intelligence/cases/ports.py`) et son implémentation par défaut
`InMemoryCaseStore` (`case_intelligence/cases/in_memory_store.py`)
attendent déjà une chaîne de caractères en clé de dictionnaire (`dict[str,
CaseProfile]`) — jamais un `uuid.UUID`. Tout consommateur d'`agent_input.
case_id` dans `tmis.agents` faisait donc déjà l'une de ces deux choses :

1. `str(agent_input.case_id) if agent_input.case_id is not None else
   None`, pour reconvertir l'UUID en chaîne avant de l'utiliser (transmis
   à `ResearchOrchestrator.search(case_id=...)`, ou passé à `CaseStorePort.
   get(...)`) ;
2. une simple comparaison `is None` / `is not None`, indifférente au type
   exact porté par le champ.

Confirmé par grep frais sur `agent_input.case_id` et `AgentInput(` dans
tout `backend/src/tmis` en Phase 0 de ce sprint (aucun nouveau
consommateur apparu depuis le Sprint 41) : **aucun** des sept agents
n'utilise une méthode spécifique à `uuid.UUID` (`.hex`, `.int`, `.bytes`,
`.version`, etc.) sur ce champ. Le changement de type consiste donc
uniquement à retirer la reconversion devenue inutile :

| Fichier | Avant | Après |
|---|---|---|
| `agents/research_agent.py:68` | `case_id = str(agent_input.case_id) if agent_input.case_id is not None else None` | `case_id = agent_input.case_id` |
| `agents/jurisprudence_agent.py:86` | idem | idem |
| `agents/watch_agent.py:96` | idem | idem |
| `agents/contract_agent.py:185` | `self._case_store.get(str(agent_input.case_id))` | `self._case_store.get(agent_input.case_id)` |
| `agents/analysis_agent.py:103` | idem | idem |
| `agents/synthesis_agent.py:84` | `case_id = str(agent_input.case_id)` | `case_id = agent_input.case_id` |

Les comparaisons `is None`/`is not None` (`contract_agent.py`,
`analysis_agent.py`) et les f-strings d'avertissement (`f"Case
{agent_input.case_id} was not found..."`) n'ont pas besoin d'être
modifiées : elles fonctionnaient déjà indépendamment du type exact du
champ.

## Les quatre points d'appel API : simplification, pas de changement de comportement

Quatre routeurs construisaient `AgentInput` avec un `case_id` reconverti
en UUID puis reperdu (`None`) si le format ne convenait pas — le
« compromis tolérant » du Sprint 41. Puisque le champ est désormais un
passe-plat direct, ce compromis n'a plus lieu d'être :

- `api/v1/chat/routes.py` (`_agent_input`) : la fonction reste (elle
  construit tout l'`AgentInput`, pas seulement `case_id`), mais son corps
  perd le `try/except uuid.UUID(...)` — `payload.case_id` (déjà une
  chaîne libre, Sprint 32) est transmis tel quel.
- `api/v1/document/routes.py` (`_parse_case_id`) : supprimé — c'était un
  passe-plat trivial une fois le `try/except` retiré ; `case_id` (le
  paramètre de requête, déjà `str | None`) est passé directement à
  `AgentInput`.
- `api/v1/watch/routes.py` (`_parse_case_id`) : supprimé, même raison.
- `api/v1/case_intelligence/routes.py` (`_parse_case_id_for_agent`) :
  supprimé, même raison — `case_id` (déjà la ressource racine de l'URL,
  `str`) est passé directement.

**Conséquence comportementale, la vraie correction de ce sprint** : un
`case_id` non-UUID comme `"case-1"` atteint désormais réellement
`CaseStorePort.get(...)` au lieu d'être silencieusement perdu à `None`.
Sur `GET /cases/{case_id}/analysis`, un dossier existant avec un `case_id`
non-UUID produit maintenant une synthèse réellement peuplée
(`result["synthesis"]["executive_summary"]` non vide), là où le Sprint 41
documentait — comme un compromis assumé, pas un bug — une synthèse vide
avec l'avertissement « No case_id provided ». C'est exactement la dette
que ce sprint corrige, voir `test_analysis_with_a_non_uuid_case_id_now_
populates_the_synthesis` (renommé et adapté depuis le test Sprint 41 `test_
analysis_with_a_non_uuid_case_id_still_succeeds`, qui vérifiait
l'inverse).

## `platform_sdk/agent_sdk/base.py` : un vrai changement de comportement, pas une simplification cosmétique

Découvert en Phase 0 de ce sprint : un cinquième point d'appel construit
`AgentInput` d'une façon différente des quatre routeurs ci-dessus.
`BaseAgentPlugin.invoke()` (le point d'entrée uniforme de l'AGENT SDK,
`PluginPort.invoke()`, consommé par tout plugin agent tiers) faisait :

```python
case_id=uuid.UUID(str(payload["case_id"])) if payload.get("case_id") else None,
```

Contrairement au « parsing tolérant » des quatre routeurs (`try/except`
qui dégrade vers `None`), cette ligne ne rattrapait **aucune** exception :
un `payload["case_id"]` qui ne parse pas comme UUID levait une
`ValueError` non gérée, faisant échouer tout l'appel `invoke()` — un
crash, pas une dégradation silencieuse. N'importe quel plugin agent tiers
invoqué avec un `case_id` de la forme `"case-1"` (le format `CaseStorePort`
accepte nativement) plantait avant même d'atteindre `run()`.

**Changement appliqué** :

```python
# Sprint 42: was `uuid.UUID(str(payload["case_id"]))`, which raised
# ValueError for any non-UUID case_id (CaseStorePort accepts free-form
# ids). Behavior change: a non-UUID case_id no longer crashes invoke().
case_id=str(payload["case_id"]) if payload.get("case_id") else None,
```

**Ce changement de comportement est déclaré explicitement, pas noyé dans
le reste du diff** (voir le commentaire inline ci-dessus, ce document, et
le rapport d'architecture) : avant ce sprint, `invoke()` levait une
`ValueError` pour tout `case_id` non-UUID ; après ce sprint, `invoke()` ne
lève plus jamais sur ce champ — un `case_id` non-UUID est transmis tel
quel à `AgentInput.case_id`, exactement comme les quatre routeurs API le
font désormais. Test dédié :
`test_agent_plugin_invoke_no_longer_raises_on_a_non_uuid_case_id`
(`tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py`).

## Ce qui n'est pas touché

- `ai_team/coordinator/engine.py:135` passe toujours `case_id=None` —
  aucun changement nécessaire, le type plus large (`str | None` au lieu de
  `uuid.UUID | None`) reste compatible tel quel avec une valeur `None`.
  L'absence de propagation d'un `case_id` réel à cet endroit reste hors
  périmètre de ce sprint (comme elle l'était déjà au Sprint 41).
- `CaseStorePort`/`CaseProfile` (`case_intelligence/cases/`) : non
  modifiés — c'est leur forme (identifiants libres) qui motive ce
  changement de type côté `AgentInput`, pas l'inverse.
- La logique métier des six agents au-delà du traitement de `case_id` :
  aucun autre comportement ne change.

## Vérification

- Suite pytest complète (`pytest -q` depuis `backend/`) : voir
  `docs/reports/sprint-42-rapport-audit.md` pour le compte exact.
- `ruff check` et `mypy --strict` verts sur tout le périmètre modifié.
- Un test par agent (les six listés) confirmant qu'un `case_id` non-UUID
  (`"case-1"`) est désormais correctement résolu — soit contre
  `CaseStorePort` (`ContractAgent`, `AnalysisAgent`, `JurisprudenceAgent`,
  `SynthesisAgent`), soit transmis tel quel à
  `ResearchOrchestrator.search()`/son historique (`ResearchAgent`,
  `WatchAgent`), là où il était auparavant silencieusement perdu.
- Un test confirmant que `platform_sdk/agent_sdk/base.py` ne lève plus sur
  un `case_id` non-UUID.
