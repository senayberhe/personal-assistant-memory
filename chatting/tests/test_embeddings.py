from assistant.memory.embeddings import (
    SimpleEmbeddingService,
)


def test_embedding_has_expected_dimensions():
    service = SimpleEmbeddingService(
        dimensions=32
    )

    vector = service.embed("Python")

    assert len(vector) == 32


def test_embedding_is_deterministic():
    service = SimpleEmbeddingService(
        dimensions=32
    )

    first = service.embed("Python")
    second = service.embed("Python")

    assert first == second


def test_different_text_produces_vector():
    service = SimpleEmbeddingService(
        dimensions=32
    )

    first = service.embed("Python")
    second = service.embed("SQL")

    assert len(first) == len(second)