from abc import ABC, abstractmethod
import hashlib
from openai import OpenAI
from config.settings import Settings



class EmbeddingService(ABC):

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass


class SimpleEmbeddingService(EmbeddingService):
    def __init__(self, dimensions: int = 32):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        normalized = text.lower().strip()
        vector = []

        for index in range(self.dimensions):
            value = hashlib.sha256(
                f"{normalized}:{index}".encode()
            ).digest()[0]

            vector.append(
                value/255.0
            )
        return vector


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, settings: Settings):
        self.client=OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.api_timeout,
        )
        self.model = settings.embedding_model


    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding