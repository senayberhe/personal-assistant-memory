from assistant.memory.embeddings import EmbeddingService
from assistant.memory.storage.base import MemoryStore
from assistant.memory.retrieval.base import RetrievedMemory, Retriever
from assistant.memory.similarity import cosine_similarity


class InMemoryRetriever(Retriever):

    def __init__(
        self,
        memory_store: MemoryStore,
        embedding_service: EmbeddingService,
    ):
        self.memory_store = memory_store
        self.embedding_service = embedding_service

    def retrieve_scored(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[RetrievedMemory]:

        if not query.strip():
            return []

        query_vector = (
            self.embedding_service.embed(query)
        )

        scored_memories = []

        for memory in self.memory_store.get_all():

            if (
                memory_type is not None
                and memory.memory_type != memory_type
            ):
                continue

            memory_vector = (
                self.embedding_service.embed(
                    memory.content
                )
            )

            score = cosine_similarity(
                query_vector,
                memory_vector,
            )

            scored_memories.append(
                RetrievedMemory(
                    memory=memory,
                    score=score,
                )
            )

        scored_memories.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return scored_memories[:top_k]
