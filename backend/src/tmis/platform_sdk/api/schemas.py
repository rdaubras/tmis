from datetime import datetime

from pydantic import BaseModel


class PluginManifestResponse(BaseModel):
    id: str
    name: str
    version: str
    plugin_type: str
    author: str
    description: str
    license: str
    permissions: list[str]
    dependencies: list[str]
    compatibility: str
    status: str
    signature: str | None


class ValidationIssueResponse(BaseModel):
    field: str
    message: str


class ValidationReportResponse(BaseModel):
    plugin_id: str
    is_valid: bool
    issues: list[ValidationIssueResponse]


class PublishingActionRequest(BaseModel):
    actor: str
    reason: str | None = None


class PublishingEventResponse(BaseModel):
    id: str
    from_status: str
    to_status: str
    actor: str
    reason: str | None
    created_at: datetime


class InstallRequest(BaseModel):
    firm_id: str
    permissions: list[str]


class ExtensionInstanceResponse(BaseModel):
    id: str
    firm_id: str
    plugin_id: str
    version: str
    status: str
    granted_permissions: list[str]
    installed_at: datetime
    updated_at: datetime


class ReviewRequest(BaseModel):
    firm_id: str
    rating: int
    comment: str = ""


class ReviewResponse(BaseModel):
    id: str
    plugin_id: str
    firm_id: str
    rating: int
    comment: str
    created_at: datetime


class MarketplaceListingResponse(BaseModel):
    manifest: PluginManifestResponse
    average_rating: float
    review_count: int
    install_count: int


class PortalResourceResponse(BaseModel):
    id: str
    title: str
    type: str
    path: str
    summary: str
