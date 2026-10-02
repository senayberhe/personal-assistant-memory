from unittest.mock import MagicMock
from assistant.embeddings import OpenAIEmbeddingService


def test_openai_embedding_service():
    settings = MagicMock()
    settings.openai_api_key = "test_api_key"
    settings.api_timeout = 30
    settings.embedding_model = "text-embedding-3-small"

    service = OpenAIEmbeddingService(settings)
    service.client=MagicMock()
    fake_response = MagicMock()

    fake_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]

    service.client.embeddings.create.return_value = fake_response

    result = service.embed("Python")

    assert result == [0.1, 0.2, 0.3]

    service.client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input="Python"
    )