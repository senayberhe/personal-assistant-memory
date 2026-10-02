from assistant.embeddings import EmbeddingService
from assistant.chroma_memory_store import memory_from_chroma
from assistant.retrieval import RetrievedMemory, Retriever


class ChromaRetriever(Retriever):

    def __init__(
        self,
        collection,
        embedding_service: EmbeddingService,
    ):
        self.collection = collection
        self.embedding_service = embedding_service

    def retrieve_scored(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[RetrievedMemory]:

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        query_embedding = (
            self.embedding_service.embed(query)
        )

        query_kwargs = {}

        if memory_type is not None:
            query_kwargs["where"] = {
                "memory_type": memory_type
            }

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
            **query_kwargs,
        )

        memories = []

        documents = results.get(
            "documents",
            [[]],
        )[0]

        ids = results.get(
            "ids",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        for index, memory_id in enumerate(ids):

            memory = memory_from_chroma(
                memory_id,
                documents[index],
                metadatas[index],
            )

            memories.append(
                RetrievedMemory(
                    memory=memory,
                    # Cosine distance -> similarity.
                    score=1.0 - distances[index],
                )
            )

        return memories
