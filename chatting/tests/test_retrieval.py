from datetime import datetime

from assistant.memory.embeddings import (
    SimpleEmbeddingService,
)
from assistant.memory.retrieval.in_memory import (
    InMemoryRetriever,
)
from assistant.memory.storage.in_memory import (
    InMemoryStore,
)
from assistant.memory import Memory


def test_retriever_returns_memories():

    store = InMemoryStore()

    store.save(
        Memory(
            id="1",
            content="User likes Python.",
            created_at=datetime.now(),
            memory_type="preference",
        )
    )

    store.save(
        Memory(
            id="2",
            content="User likes coffee.",
            created_at=datetime.now(),
            memory_type="preference",
        )
    )

    embedding_service = SimpleEmbeddingService()

    retriever = InMemoryRetriever(
        memory_store=store,
        embedding_service=embedding_service,
    )

    results = retriever.retrieve(
        "What does the user like?",
        top_k=1,
    )

    assert len(results) == 1