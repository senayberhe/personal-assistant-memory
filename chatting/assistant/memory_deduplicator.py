from assistant.memory_model import Memory


class MemoryDeduplicator:

    def __init__(
        self,
        memory_manager,
        similarity_threshold: float = 0.90,
    ):
        self.memory_manager = memory_manager
        self.similarity_threshold = (
            similarity_threshold
        )

    def find_duplicate(
        self,
        content: str,
    ) -> Memory | None:

        results = (
            self.memory_manager.recall_scored(
                query=content,
                top_k=1,
            )
        )

        if not results:
            return None

        best_match = results[0]

        if (
            best_match.score
            >= self.similarity_threshold
        ):
            return best_match.memory

        return None