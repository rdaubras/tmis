from tmis.platform_sdk.developer_portal.schemas import PortalResource, ResourceType

_CATALOG: tuple[PortalResource, ...] = (
    PortalResource(
        "guide-developpeur",
        "Guide développeur TMIS",
        ResourceType.GUIDE,
        "docs/66-guide-developpeur.md",
        "Comment démarrer : structure d'un plugin, cycle de vie, premiers pas.",
    ),
    PortalResource(
        "guide-sdk",
        "Guide du SDK TMIS",
        ResourceType.GUIDE,
        "docs/67-guide-sdk.md",
        "Le contrat PluginPort/PluginContext commun à tous les types de plugin.",
    ),
    PortalResource(
        "guide-marketplace",
        "Guide de la Marketplace",
        ResourceType.GUIDE,
        "docs/68-guide-marketplace.md",
        "Catalogue, recherche, avis, installation, mise à jour, désinstallation.",
    ),
    PortalResource(
        "guide-plugins",
        "Guide des Plugins",
        ResourceType.GUIDE,
        "docs/69-guide-plugins.md",
        "Manifeste, permissions, sandbox, cycle de vie de publication.",
    ),
    PortalResource(
        "guide-workflows",
        "Guide des Workflows",
        ResourceType.GUIDE,
        "docs/70-guide-workflows.md",
        "Définir un workflow déclaratif : étapes, conditions, actions, export/import.",
    ),
    PortalResource(
        "guide-connecteurs",
        "Guide des Connecteurs",
        ResourceType.GUIDE,
        "docs/71-guide-connecteurs.md",
        "Authentification, pagination, cache et normalisation pour un connecteur.",
    ),
    PortalResource(
        "reference-api",
        "Référence API du Platform SDK",
        ResourceType.API_REFERENCE,
        "docs/72-reference-api-platform-sdk.md",
        "Tous les endpoints REST exposés par tmis.platform_sdk.",
    ),
    PortalResource(
        "tutoriel-premier-plugin",
        "Tutoriel : créer son premier agent",
        ResourceType.TUTORIAL,
        "docs/66-guide-developpeur.md#tutoriel",
        "Pas à pas : scaffold, implémentation, validation, publication, installation.",
    ),
    PortalResource(
        "exemple-agent-fiscal",
        "Exemple : Agent Fiscal",
        ResourceType.EXAMPLE,
        "backend/src/tmis/platform_sdk/examples/agent_fiscal.py",
        "Un agent complet construit sur agent_sdk.",
    ),
    PortalResource(
        "exemple-agent-droit-social",
        "Exemple : Agent Droit Social",
        ResourceType.EXAMPLE,
        "backend/src/tmis/platform_sdk/examples/agent_droit_social.py",
        "Un second agent, pour montrer la réutilisation du même SDK.",
    ),
    PortalResource(
        "exemple-connecteur-ged",
        "Exemple : Connecteur GED",
        ResourceType.EXAMPLE,
        "backend/src/tmis/platform_sdk/examples/connector_ged.py",
        "Un connecteur avec pagination, cache et normalisation.",
    ),
    PortalResource(
        "exemple-workflow-validation",
        "Exemple : Workflow de validation",
        ResourceType.EXAMPLE,
        "backend/src/tmis/platform_sdk/examples/workflow_validation.py",
        "Un workflow déclaratif à embranchement conditionnel.",
    ),
    PortalResource(
        "exemple-modele-consultation",
        "Exemple : Modèle de consultation",
        ResourceType.EXAMPLE,
        "backend/src/tmis/platform_sdk/examples/document_template_consultation.py",
        "Un modèle documentaire avec variables et sections.",
    ),
    PortalResource(
        "bonnes-pratiques-permissions",
        "Bonnes pratiques : demander le minimum de permissions",
        ResourceType.BEST_PRACTICE,
        "docs/69-guide-plugins.md#bonnes-pratiques",
        "Ne déclarer que les permissions réellement utilisées par le plugin.",
    ),
)


class DeveloperPortalService:
    """The sprint's "DEVELOPER PORTAL" spec: tutoriels, guides,
    références API, exemples, bonnes pratiques — a small catalog of
    metadata pointing at the real documentation/example files rather
    than a documentation engine of its own."""

    def list_all(self) -> tuple[PortalResource, ...]:
        return _CATALOG

    def list_by_type(self, resource_type: ResourceType) -> tuple[PortalResource, ...]:
        return tuple(r for r in _CATALOG if r.type is resource_type)

    def search(self, keyword: str) -> tuple[PortalResource, ...]:
        needle = keyword.lower()
        return tuple(
            r
            for r in _CATALOG
            if needle in r.title.lower() or needle in r.summary.lower()
        )
