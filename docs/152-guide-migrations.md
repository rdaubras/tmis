# 152 — Guide : ajouter une migration Alembic

Le dépôt a une seule configuration Alembic (`backend/alembic.ini`,
`backend/alembic/env.py`) et une seule base déclarative
(`tmis.core.db.base.Base`, qui réexporte `tmis.core.database.Base` —
voir docs/151-architecture-persistance.md). N'en créez jamais une
seconde : une nouvelle migration s'ajoute toujours à cette même chaîne.

## Avant d'écrire une migration

1. Le modèle SQLAlchemy existe déjà dans
   `<domaine>/adapters/sqlalchemy_store.py` (ou, pour les deux domaines
   qui avaient déjà un fichier `adapters.py` pour un autre usage —
   `legal_drafting.documents` et `legal_reasoning.reasoner` — dans
   `<domaine>/sqlalchemy_store.py`, en fichier frère). Les migrations de
   ce dépôt sont écrites à la main, jamais générées par
   `alembic revision --autogenerate` (qui exigerait une base réelle déjà
   à jour) — mais elles doivent rester le miroir exact des `mapped_column`
   du modèle.
2. Le module du modèle doit être importé dans `backend/alembic/env.py`
   (liste d'imports en tête de fichier, un par domaine) pour que
   `Base.metadata` le connaisse — nécessaire seulement si vous voulez un
   jour utiliser `--autogenerate` en complément ; les migrations restent
   écrites à la main.

## Écrire la migration

1. Choisissez le prochain numéro (`000N_nom_du_domaine.py`) et créez le
   fichier dans `backend/alembic/versions/`.
2. `revision` = le nom du fichier sans l'extension (ex.
   `"0008_mon_domaine"`). `down_revision` = la `revision` de la migration
   précédente dans la chaîne (vérifiez avec `alembic history`, voir plus
   bas) — jamais `None` sauf pour `0000_base_identity`, la racine de la
   chaîne (voir "Chaîne autoportante" ci-dessous ; `0001_document_record`
   n'est plus la racine depuis le correctif SEC/DB-01).
3. `upgrade()` : `op.create_table(...)` avec exactement les colonnes du
   modèle (mêmes noms, mêmes types, mêmes contraintes). Utilisez
   `sa.Uuid()` (portable, pas le type PostgreSQL-only
   `postgresql.UUID`) et `sa.JSON()` pour les colonnes JSON — les deux
   fonctionnent aussi bien sous PostgreSQL (production) que SQLite
   (tests, voir plus bas), contrairement à des types spécifiques à un
   dialecte.
4. `downgrade()` : l'inverse exact (`op.drop_index()` puis
   `op.drop_table()`), jamais un `pass`.
5. N'enrichissez jamais le schéma métier au passage : les colonnes
   reflètent fidèlement les champs du dataclass existant. Si un besoin de
   colonne supplémentaire apparaît (index technique, clé de version...),
   documentez pourquoi dans le docstring du modèle — voir
   `tmis.document_intelligence.adapters.sqlalchemy_store` pour un exemple
   (`version`/`previous_version_id`, nécessaires au versionning demandé
   par le sprint, pas un enrichissement du `DocumentRecord` lui-même).

## Vérifier la chaîne

```bash
cd backend
TMIS_DATABASE_URL="sqlite:////tmp/migration_check.db" python3 -m alembic history
TMIS_DATABASE_URL="sqlite:////tmp/migration_check.db" python3 -m alembic upgrade head
TMIS_DATABASE_URL="sqlite:////tmp/migration_check.db" python3 -m alembic downgrade base
rm -f /tmp/migration_check.db
```

`TMIS_DATABASE_URL` redirige `Settings.database_url` (préfixe d'env
`TMIS_`, voir `tmis.core.config`) vers une base SQLite jetable — c'est le
plus rapide moyen de vérifier qu'une migration s'applique et se défait
proprement sans dépendre d'un vrai Postgres. En production/CI,
`alembic upgrade head` s'exécute contre le `database_url` réel (Postgres).

## Tests

Chaque adaptateur `SQLAlchemy*Store` a un test d'intégration dédié dans
`backend/tests/integration/<domaine>/` qui crée son propre moteur SQLite
(`create_engine("sqlite:///:memory:", ...)` + `Base.metadata.create_all`
limité à sa seule table) — ces tests n'exécutent pas les migrations
elles-mêmes, ils valident le modèle. La vérification de la chaîne
Alembic complète (ci-dessus) est un contrôle séparé, à refaire à chaque
migration ajoutée.

`tests/integration/test_schema_parity.py` (correctif SEC/DB-01) est le
garde-fou qui aurait attrapé le bug ce correctif corrige — jusqu'ici,
tous les tests créaient leurs tables via `Base.metadata.create_all()`,
jamais via `alembic upgrade head`, donc rien ne remarquait qu'un modèle
sans migration correspondante (`firms`/`users`/`cases`, jamais migrées)
laissait un `alembic upgrade head` sur base vierge produire un schéma
incomplet. Ce test applique la chaîne réelle sur une base neuve et
compare le résultat (tables, puis colonnes par table) à `Base.metadata` —
un modèle ajouté sans sa migration, ou une migration créant une table
sans modèle, le fait désormais échouer. **Toute nouvelle migration doit
laisser ce test vert** ; ce n'est pas optionnel.

## Chaîne autoportante (correctif SEC/DB-01)

`0000_base_identity` (racine de la chaîne) crée `firms`/`users`/`cases` —
les seules tables du schéma qui n'avaient jamais eu leur propre migration
(elles préexistaient à Alembic dans ce dépôt, créées uniquement via
`Base.metadata.create_all()`, que tous les tests utilisent à la place des
migrations réelles). `alembic upgrade head` sur une base vierge est
désormais autoportant : il produit le schéma complet, y compris ces
fondations, sans dépendre d'une base déjà amorcée par ailleurs. Les
migrations de rétro-remplissage (`0012_case_profiles_firm_id`,
`0013_document_records_firm_id`) qui dérivent `firm_id` depuis `cases`
n'émettent donc plus l'avertissement "no 'cases' table found" sur un
premier déploiement.

Les bases dev/staging déjà amorcées via `create_all()` (donc déjà à
`0013` dans `alembic_version`) ne sont pas concernées : `firms`/`users`/
`cases` existent déjà physiquement chez elles, et Alembic ne rejoue
jamais une migration déjà marquée comme appliquée. Ce correctif ne
change rien pour elles ; il ne vise que les déploiements propres.
