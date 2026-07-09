from tmis.ai.schemas.citation import Citation, RetrievedChunk
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


def test_model_response_total_tokens() -> None:
    response = ModelResponse(
        text="hello", provider="openai", model="gpt-4o", prompt_tokens=3, completion_tokens=5
    )
    assert response.total_tokens == 8


def test_provider_capabilities_defaults() -> None:
    caps = ProviderCapabilities()
    assert caps.supports_completion is True
    assert caps.supports_embeddings is False


def test_connector_document_defaults_metadata() -> None:
    doc = ConnectorDocument(id="1", title="t", content="c", connector="codes")
    assert doc.metadata == {}


def test_retrieved_chunk_to_citation() -> None:
    chunk = RetrievedChunk(
        chunk_id="c1", document_id="d1", content="excerpt text", score=0.9, metadata={}
    )
    citation = chunk.to_citation(connector="rag", reference="d1")
    assert citation == Citation(
        source_id="c1", connector="rag", excerpt="excerpt text", reference="d1"
    )
