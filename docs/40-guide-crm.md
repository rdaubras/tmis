# Guide — CRM

## Personnes physiques et personnes morales

`tmis.cabinet_os.clients.schemas.ClientType` : `INDIVIDUAL` ou
`ORGANIZATION`. Les champs spécifiques à chaque type
(`first_name`/`last_name` pour un individu, `legal_form`/
`registration_number`/`vat_number` pour une organisation) coexistent
sur le même agrégat `Client`, vides pour le type qui ne les utilise
pas — un cabinet n'a jamais besoin de savoir, en amont, lequel des deux
formulaires afficher pour lire un client existant.

## Cycle de vie d'un client

```python
from tmis.cabinet_os.clients.schemas import ClientStatus, ClientType
from tmis.cabinet_os.clients.service import ClientService

service = ClientService()
client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")
service.change_status(client.id, ClientStatus.ACTIVE, actor_id="admin-1")
```

Transitions autorisées : `PROSPECT → ACTIVE`, `PROSPECT → ARCHIVED`,
`ACTIVE → ARCHIVED`, `ARCHIVED → ACTIVE` (réactivation). Chaque
transition est **ajoutée** à `Client.history`, jamais réécrite.

## Notes

```python
service.add_note(client.id, "author-1", "Premier rendez-vous effectué")
```

Les notes s'accumulent dans `Client.notes` — un historique de
correspondance/suivi, distinct du journal de statut.

## Liens vers dossiers, documents et contacts

`Client` ne stocke que des ids (`case_ids`, `document_ids`,
`contact_ids`, `invoice_ids`) :

```python
service.link_case(client.id, case_id)
service.link_document(client.id, document_id)
service.link_contact(client.id, contact_id)
```

## Contacts et relations

`tmis.cabinet_os.contacts.schemas.ContactRole` couvre les six
catégories du brief : `EXECUTIVE`, `REPRESENTATIVE`, `EXPERT`,
`WITNESS`, `ADMINISTRATION`, `PARTNER`. Les contacts peuvent être
reliés entre eux :

```python
from tmis.cabinet_os.contacts.schemas import ContactRelationType
from tmis.cabinet_os.contacts.service import ContactService

contacts = ContactService()
executive = contacts.create("firm-1", ContactRole.EXECUTIVE, "Mme Directrice")
representative = contacts.create("firm-1", ContactRole.REPRESENTATIVE, "M. Avocat")
contacts.relate("firm-1", representative.id, executive.id, ContactRelationType.REPRESENTS)
```

## La vue à 360° : `CRMEngine`

```python
from tmis.cabinet_os.crm.engine import CRMEngine

crm = CRMEngine(client_store, contact_store)
profile = crm.get_profile(client.id)
# profile.client, profile.contacts (résolus), profile.case_ids,
# profile.document_ids, profile.invoice_ids (juste les ids)
```

`CRMEngine` ne stocke rien : il résout les ids d'un `Client` en objets
`Contact` complets pour la vue à 360°. Les dossiers, documents et
factures restent des ids — leurs détails vivent dans leurs moteurs
respectifs (`case_intelligence`, `cabinet_os.documents`,
`cabinet_os.billing`).

## Recherche

```python
crm.search("firm-1", "dupont")  # nom ou email, insensible à la casse
crm.search("firm-1", "")        # tous les clients du cabinet
```
