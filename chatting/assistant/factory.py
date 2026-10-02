from assistant.agent import VoiceAgent
from assistant.application import Application
from assistant.assistant import VoiceAssistant
from assistant.chroma_memory_history_store import (
    ChromaMemoryHistoryStore,
)
from assistant.chroma_memory_store import (
    ChromaMemoryStore,
)
from assistant.chroma_retriever import ChromaRetriever
from assistant.embeddings import OpenAIEmbeddingService
from assistant.executor import ToolExecutor
from assistant.health import (
    HealthCheckResult,
    HealthChecker,
)
from assistant.memory_extractor import MemoryExtractor
from assistant.memory_manager import MemoryManager
from assistant.permissions import PermissionManager
from assistant.registry import ToolRegistry
from assistant.security import SecurityPolicy
from assistant.tools import (
    AssistantTools,
    build_tool_definitions,
)
from config.settings import Settings
from services.speech import SpeechService
from services.tts import TTSService


class ApplicationFactory:
    """
    Builds and wires together all components of the
    voice assistant application.

    The factory acts as the composition root.
    """

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    def create(self) -> Application:
        """
        Create the complete voice assistant application.
        """

        # --------------------------------------------------
        # Speech and text-to-speech
        # --------------------------------------------------

        speech = SpeechService(
            timeout=self.settings.speech_timeout,
            phrase_time_limit=(
                self.settings.phrase_time_limit
            ),
            ambient_noise_duration=(
                self.settings.ambient_noise_duration
            ),
        )

        tts = TTSService()

        # --------------------------------------------------
        # Tools
        # --------------------------------------------------

        assistant_tools = AssistantTools()

        registry = ToolRegistry()

        assistant_tools.register_tools(
            registry
        )

        # --------------------------------------------------
        # Security
        # --------------------------------------------------

        security_policy = SecurityPolicy()

        permissions = PermissionManager(
            security_policy=security_policy
        )

        executor = ToolExecutor(
            registry=registry,
            permission_manager=permissions,
        )

        tool_definitions = (
            build_tool_definitions()
        )

        # --------------------------------------------------
        # Persistent memory
        # --------------------------------------------------

        # Embeddings: the store and the retriever must use
        # the same service, or stored and query vectors
        # will have different sizes.
        embedding_service = (
            OpenAIEmbeddingService(
                settings=self.settings
            )
        )

        memory_store = ChromaMemoryStore(
            persist_directory=(
                self.settings.memory_directory
            ),
            collection_name=(
                "assistant_memories"
            ),
            embedding_service=embedding_service,
        )

        # --------------------------------------------------
        # Memory retrieval
        # --------------------------------------------------

        retriever = ChromaRetriever(
            collection=memory_store.collection,
            embedding_service=embedding_service,
        )

        # --------------------------------------------------
        # Persistent memory history
        # --------------------------------------------------

        history_store = (
            ChromaMemoryHistoryStore(
                persist_directory=(
                    self.settings.memory_directory
                ),
                collection_name=(
                    "assistant_memory_history"
                ),
            )
        )

        # --------------------------------------------------
        # Memory manager
        # --------------------------------------------------

        memory_manager = MemoryManager(
            store=memory_store,
            retriever=retriever,
            history_store=history_store,
        )

        # --------------------------------------------------
        # Memory extraction
        # --------------------------------------------------

        memory_extractor = MemoryExtractor()

        # --------------------------------------------------
        # AI agent
        # --------------------------------------------------

        agent = VoiceAgent(
            executor=executor,
            tool_definitions=tool_definitions,
            settings=self.settings,
            memory_manager=memory_manager,
            memory_extractor=memory_extractor,
        )

        # --------------------------------------------------
        # Voice assistant
        # --------------------------------------------------

        voice_assistant = VoiceAssistant(
            speech_service=speech,
            agent=agent,
            tts_service=tts,
        )

        # --------------------------------------------------
        # Health checks
        # --------------------------------------------------

        health_checker = HealthChecker(
            checks=[
                lambda: self._check_microphone(
                    speech
                ),
                lambda: self._check_memory_store(
                    memory_store
                ),
            ]
        )

        # --------------------------------------------------
        # Application
        # --------------------------------------------------

        return Application(
            assistant=voice_assistant,
            health_checker=health_checker,
        )

    @staticmethod
    def _check_microphone(
        speech: SpeechService,
    ) -> HealthCheckResult:
        """
        Check whether the microphone is available.
        """

        healthy = speech.health_check()

        if healthy:
            return HealthCheckResult(
                name="microphone",
                healthy=True,
                message=(
                    "Microphone is available."
                ),
            )

        return HealthCheckResult(
            name="microphone",
            healthy=False,
            message=(
                "Microphone is unavailable."
            ),
        )

    @staticmethod
    def _check_memory_store(
        memory_store: ChromaMemoryStore,
    ) -> HealthCheckResult:
        """
        Check whether the memory database can be read.
        """

        try:
            count = memory_store.collection.count()

        except Exception as error:
            return HealthCheckResult(
                name="memory",
                healthy=False,
                message=(
                    f"Memory store is unavailable: {error}"
                ),
            )

        return HealthCheckResult(
            name="memory",
            healthy=True,
            message=(
                f"Memory store is available "
                f"({count} memories)."
            ),
        )
