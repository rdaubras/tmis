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
   du modèle. Seule exception à ce jour : `0000_base_identity` (`firms`/
   `users`/`cases`, correctif SEC/DB-01), dont les colonnes `Enum` Postgres
   ont été obtenues via `--autogenerate` contre une base réelle déjà à
   `0013`, puis élaguées pour ne garder que ces trois tables — précisément
   pour éviter d'écrire les types ENUM à la main et diverger de ce que
   `create_all` génère. Repartez de cette méthode si une future migration
   introduit elle aussi une colonne `Enum` Python.
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
   chaîne.
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

`backend/tests/integration/test_schema_parity.py` fait ce contrôle en
continu, en CI : il exécute la chaîne Alembic complète sur une base
vierge et compare le jeu de tables (et de colonnes) obtenu à
`Base.metadata.tables`. Si vous ajoutez un modèle sans lui écrire de
migration (ou une migration `create_table` sans modèle correspondant),
ce test échoue — c'est le garde-fou qui a motivé le correctif SEC/DB-01
(`0000_base_identity`), voir docs/151-architecture-persistance.md. Si
votre nouveau module de modèle vit dans un fichier que `backend/alembic/
env.py` n'importe pas encore, ajoutez-y l'import (même règle que le
point 2 ci-dessus) **et** dans `test_schema_parity.py`, sinon
`Base.metadata` ne le verra pas et le test ne pourra pas le comparer.
