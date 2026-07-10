import io

from PIL import Image

from tmis.document_intelligence.schemas.document import IngestedDocument


class ImageParser:
    """Implements `DocumentParserPort` for scanned images (JPEG, PNG).

    Text extraction from the image itself is the OCR stage's
    responsibility (`tmis.document_intelligence.ocr`), not the parser's:
    this parser only validates the image and captures its intrinsic
    metadata (dimensions, format), leaving `text` empty.
    """

    content_types: tuple[str, ...] = ("image/jpeg", "image/png")

    def supports(self, content_type: str) -> bool:
        return content_type in self.content_types

    def parse(self, document_id: str, filename: str, raw_bytes: bytes) -> IngestedDocument:
        with Image.open(io.BytesIO(raw_bytes)) as image:
            width, height = image.size
            image_format = image.format or "unknown"

        return IngestedDocument(
            id=document_id,
            filename=filename,
            content_type=f"image/{image_format.lower()}",
            text="",
            page_count=1,
            raw_bytes=raw_bytes,
            metadata={"width": str(width), "height": str(height), "format": image_format},
        )
