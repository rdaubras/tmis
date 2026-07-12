from tmis.business_platform.tenant_settings.ports import TenantSettingsStorePort
from tmis.business_platform.tenant_settings.schemas import InvoicingLanguage, TenantSettings


class TenantSettingsEngine:
    def __init__(self, store: TenantSettingsStorePort) -> None:
        self._store = store

    def get_or_default(self, firm_id: str) -> TenantSettings:
        settings = self._store.get(firm_id)
        if settings is None:
            settings = TenantSettings(firm_id=firm_id)
            self._store.save(settings)
        return settings

    def update(
        self,
        firm_id: str,
        *,
        currency: str | None = None,
        invoicing_language: InvoicingLanguage | None = None,
        invoicing_contact_email: str | None = None,
        auto_renew: bool | None = None,
    ) -> TenantSettings:
        settings = self.get_or_default(firm_id)
        if currency is not None:
            settings.currency = currency
        if invoicing_language is not None:
            settings.invoicing_language = invoicing_language
        if invoicing_contact_email is not None:
            settings.invoicing_contact_email = invoicing_contact_email
        if auto_renew is not None:
            settings.auto_renew = auto_renew
        self._store.save(settings)
        return settings
