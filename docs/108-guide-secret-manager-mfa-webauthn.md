# Guide — Secret Manager, MFA & WebAuthn (Sprint 19)

## Secret Manager — jamais de secret en clair

`secret_manager.SecretManagerEngine` compose directement
`platform.security.encryption`/`secrets_rotation.RotatingEncryption`
(Sprint 10) — même convention de réutilisation que
`integration_hub.security` (Sprint 18).

```python
secret = engine.set_secret(firm_id, "crm-api-key", "valeur-en-clair")
# secret.encrypted_value ne contient jamais "valeur-en-clair"
plaintext = engine.get_secret(firm_id, "crm-api-key")  # déchiffre à la demande
```

`SecretManagerEngine.list_for_firm` (et l'endpoint `GET
/identity-platform/secrets`) n'exposent que les métadonnées
(`key`, `firm_id`, `created_at`, `rotated_at`, `encrypted_value` — un
texte chiffré, jamais du clair) : aucun appelant ne peut lire un
secret en masse sans passer par `get_secret` explicitement. Le
contrôle d'accès est délégué à l'appelant via `authorization.
AuthorizationEngine` (`Permission.SECRET_MANAGE`, accordée à
`Role.IT_ADMIN` par défaut) ; la journalisation passe par
`security_events`.

## MFA — TOTP (RFC 6238)

`mfa.MfaEngine` implémente TOTP depuis la stdlib
(`hmac`/`hashlib`/`struct`/`base64`/`secrets`, aucune dépendance
`pyotp` ajoutée) :

```python
enrollment = mfa.enroll(firm_id, user_id)      # génère un secret base32
mfa.confirm(firm_id, user_id, code_from_app)   # ne devient actif qu'une fois prouvé
mfa.verify(firm_id, user_id, code_from_app)    # vérifie un login ultérieur
```

Un enrôlement reste `confirmed=False` tant que l'utilisateur n'a pas
prouvé qu'il génère un code valide — un secret mal recopié ne peut
jamais verrouiller silencieusement un compte dans un état MFA cassé.
`verify_totp` accepte une fenêtre de ±1 pas de temps (30s) pour
tolérer la dérive d'horloge, pratique standard TOTP.

## WebAuthn & Passkeys — cérémonie de référence

`webauthn.WebAuthnEngine` vérifie une clé publique opaque et un
compteur de signature strictement croissant (protection anti-rejeu),
mais **n'analyse aucune clé COSE réelle et ne vérifie aucune signature
cryptographique d'attestation/assertion**. Voir
docs/103-architecture-identity-platform.md pour la justification de
cette limite assumée.

```python
webauthn.register_credential(firm_id, user_id, credential_id, public_key)
webauthn.verify_assertion(firm_id, credential_id, signature_counter)  # rejette le rejeu
```

`passkeys.PasskeyEngine` compose `WebAuthnEngine` pour l'authentification
*usernameless* : le compteur de signature est vérifié en premier, puis
l'utilisateur est résolu depuis le `credential_id` — jamais l'inverse
(un credential révoqué/rejoué ne doit jamais révéler l'identité qu'il
usurpe).

## Passwordless & Magic Link

`passwordless.PasswordlessEngine` émet un code à 6 chiffres à usage
unique, expirant après 10 minutes, livré hors bande par l'appelant
(SMS/email — ce moteur reste agnostique du canal). `magic_links.
MagicLinkEngine` réutilise directement `tmis.core.security.
create_access_token`/`decode_access_token` (JWT) avec un claim
`purpose="magic_link"`, et un store de jetons déjà consommés pour le
rendre à usage unique malgré la nature normalement stateless d'un JWT.
