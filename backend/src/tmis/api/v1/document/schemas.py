from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    task_id: str
    status: str


class DocumentVersionResponse(BaseModel):
    version: int
    filename: str
    status: str
    previous_version_id: str | None


class DocumentSummaryResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    ocr_text: str
    warnings: list[str]
