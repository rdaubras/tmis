"""Seeds an in-memory beta-pilot demonstration environment for TMIS.

Run from `backend/`: `python -m scripts.seed_beta_pilot`

Composes only engines already delivered in Sprints 4, 8, 9 and 10 — no
new business functionality is introduced. Every store used here is the
same `InMemory*` reference implementation used in tests: nothing is
written to a real database, so a pilot cabinet can re-run this freely.
"""

from tmis.cabinet_os.clients.schemas import ClientType
from tmis.cabinet_os.clients.service import ClientService
from tmis.cabinet_os.clients.store import InMemoryClientStore
from tmis.cabinet_os.subscriptions.schemas import PlanTier
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseTask
from tmis.collaboration.members.service import MemberService
from tmis.collaboration.members.store import InMemoryMemberStore
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.roles.store import InMemoryRoleAssignmentStore
from tmis.collaboration.workspace.schemas import Workspace
from tmis.collaboration.workspace.store import InMemoryWorkspaceStore
from tmis.platform.licensing.engine import LicenseEngine
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform.licensing.store import InMemoryLicenseStore

FIRM_ID = "firm-demo"
WORKSPACE_ID = "workspace-demo"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés"

_DEMO_USERS = [
    ("admin@demo.tmis.example.com", "Camille Lefèvre", Role.ADMINISTRATOR),
    ("associe@demo.tmis.example.com", "Julien Moreau", Role.ASSOCIATE),
    ("collaborateur@demo.tmis.example.com", "Sarah Nguyen", Role.COLLABORATOR),
    ("assistante@demo.tmis.example.com", "Inès Dubois", Role.ASSISTANT),
    ("client@demo.tmis.example.com", "Société Exemplia SAS", Role.CLIENT),
]

_DEMO_CASES = [
    ("case-demo-1", "Litige commercial — Exemplia SAS c. Fournitek", [
        "Analyser la clause de résiliation du contrat-cadre",
        "Préparer la mise en demeure",
    ]),
    ("case-demo-2", "Droit du travail — Contentieux licenciement M. Rousseau", [
        "Vérifier la procédure disciplinaire suivie",
        "Chiffrer l'indemnisation potentielle",
    ]),
    ("case-demo-3", "Conseil contractuel — Refonte CGV Exemplia SAS", [
        "Rédiger un projet de CGV actualisées",
        "Vérifier la conformité RGPD des clauses de données",
    ]),
]


def seed() -> None:
    licenses = LicenseEngine(InMemoryLicenseStore(), LicenseKeySigner("demo-signing-key"))
    license_ = licenses.issue(FIRM_ID, PlanTier.CABINET, duration_days=30)
    print(
        f"Licence de démonstration émise pour {FIRM_NAME}: "
        f"expire le {license_.expires_at:%Y-%m-%d}"
    )

    workspaces = InMemoryWorkspaceStore()
    workspaces.save(Workspace(id=WORKSPACE_ID, firm_id=FIRM_ID, name=FIRM_NAME))

    members = MemberService(InMemoryMemberStore())
    roles = InMemoryRoleAssignmentStore()
    for email, display_name, role in _DEMO_USERS:
        member = members.invite(WORKSPACE_ID, email, display_name)
        members.activate(member.id)
        roles.assign(WORKSPACE_ID, member.id, role)
        print(f"Utilisateur de démonstration créé: {display_name} <{email}> ({role.value})")

    clients = ClientService(InMemoryClientStore())
    clients.create(
        FIRM_ID, ClientType.ORGANIZATION, "Exemplia SAS", email="contact@exemplia.example.com"
    )
    clients.create(
        FIRM_ID,
        ClientType.INDIVIDUAL,
        "M. Antoine Rousseau",
        email="a.rousseau@example.com",
        first_name="Antoine",
        last_name="Rousseau",
    )
    print("Clients de démonstration créés: Exemplia SAS, M. Antoine Rousseau")

    cases = InMemoryCaseStore()
    for case_id, title, tasks in _DEMO_CASES:
        profile = cases.get_or_create(case_id, title)
        profile.tasks = [
            CaseTask(id=f"{case_id}-task-{i}", description=desc)
            for i, desc in enumerate(tasks, start=1)
        ]
        print(f"Dossier de démonstration créé: {title} ({len(tasks)} tâche(s))")

    print()
    print("=== Parcours d'onboarding (checklist) ===")
    print("[ ] Se connecter avec admin@demo.tmis.example.com")
    print("[ ] Consulter le tableau de bord du cabinet")
    print(f"[ ] Ouvrir le dossier '{_DEMO_CASES[0][1]}' et sa chronologie")
    print("[ ] Générer un brouillon de document sur ce dossier")
    print("[ ] Inviter un second utilisateur de démonstration et vérifier ses permissions")
    print("[ ] Consulter GET /platform/monitoring (santé + coût IA cumulé)")
    print(f"[ ] Vérifier la validité de la licence de démonstration: {license_.key[:24]}...")
    print(f"    (durée de validité: {(license_.expires_at - license_.issued_at).days} jours)")


if __name__ == "__main__":
    seed()
