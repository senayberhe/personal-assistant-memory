"""
Composition root: the only place that knows how every component is
built and connected. Everything else receives its collaborators
through its constructor, which keeps it easy to test.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from rich.console import Console

from assistant.agent import TEXT_INSTRUCTIONS, VOICE_INSTRUCTIONS, VoiceAgent
from assistant.application import Application
from assistant.health import HealthChecker, HealthCheckResult
from assistant.interfaces.commands import ChatCommands
from assistant.interfaces.prompter import RichPrompter
from assistant.interfaces.text_chat import TextChat
from assistant.interfaces.voice import VoiceAssistant
from assistant.memory import MemoryManager
from assistant.memory.audit.chroma import ChromaMemoryAuditStore
from assistant.memory.confirmation import CallbackMemoryConfirmation
from assistant.memory.embeddings import OpenAIEmbeddingService
from assistant.memory.events.audit_listener import MemoryAuditListener
from assistant.memory.events.logging_listener import MemoryLoggingListener
from assistant.memory.events.metrics import MemoryMetrics
from assistant.memory.events.metrics_listener import MemoryMetricsListener
from assistant.memory.events.publisher import MemoryEventPublisher
from assistant.memory.extractor import MemoryExtractor
from assistant.memory.history.chroma import ChromaMemoryHistoryStore
from assistant.memory.policy import MemoryPolicy
from assistant.memory.resolution.ai import AIMemoryResolver
from assistant.memory.resolution.resilient import ResilientMemoryResolver
from assistant.memory.resolution.rules import MemoryResolver
from assistant.memory.retrieval.candidate_ranker import MemoryCandidateRanker
from assistant.memory.retrieval.chroma import ChromaRetriever
from assistant.memory.retrieval.scored_candidate_retriever import (
    ScoredCandidateRetriever,
)
from assistant.memory.storage.chroma import ChromaMemoryStore
from assistant.tools.builtin import AssistantTools, build_tool_definitions
from assistant.tools.executor import ToolExecutor
from assistant.tools.permissions import PermissionManager, console_confirm
from assistant.tools.rate_limit import RateLimiter
from assistant.tools.registry import ToolRegistry
from assistant.tools.security import SecurityPolicy
from config.settings import Settings
from services.speech import SpeechService
from services.tts import TTSService

Interface = Literal["voice", "text"]

# At most this many tool calls per minute, so a looping model
# cannot spam actions (open 50 browser tabs, ...).
TOOL_CALLS_PER_MINUTE = 20

Confirm = Callable[[str], bool]


@dataclass
class _MemorySystem:
    manager: MemoryManager
    store: ChromaMemoryStore
    metrics: MemoryMetrics


class ApplicationFactory:
    """Builds the complete application for one interface."""

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    def create(
        self,
        interface: Interface = "voice",
        console: Console | None = None,
    ) -> Application:
        """
        interface:
            "voice" (microphone + speech) or "text" (terminal chat).
        console:
            Rich console for the text chat (injected in tests).
        """

        if interface == "text":
            console = console or Console()
            prompter = RichPrompter(console)
            confirm: Confirm = prompter.confirm
        else:
            confirm = console_confirm

        executor, tool_definitions = self._build_tools(confirm)
        memory = self._build_memory(confirm)

        agent = VoiceAgent(
            executor=executor,
            tool_definitions=tool_definitions,
            settings=self.settings,
            memory_manager=memory.manager,
            memory_extractor=MemoryExtractor(),
            instructions=(
                TEXT_INSTRUCTIONS if interface == "text" else VOICE_INSTRUCTIONS
            ),
        )

        checks = [lambda: self._check_memory_store(memory.store)]

        front_end: TextChat | VoiceAssistant

        if interface == "text":
            front_end = TextChat(
                agent=agent,
                commands=ChatCommands(
                    memory_manager=memory.manager,
                    reset_conversation=agent.reset_conversation,
                    confirm=confirm,
                    memory_metrics=memory.metrics,
                    tool_metrics=executor.metrics,
                ),
                prompter=prompter,
                console=console,
            )
        else:
            speech = SpeechService(
                timeout=self.settings.speech_timeout,
                phrase_time_limit=self.settings.phrase_time_limit,
                ambient_noise_duration=self.settings.ambient_noise_duration,
            )

            front_end = VoiceAssistant(
                speech_service=speech,
                agent=agent,
                tts_service=TTSService(),
            )

            checks.insert(0, lambda: self._check_microphone(speech))

        return Application(
            assistant=front_end,
            health_checker=HealthChecker(checks=checks),
            shutdown_hooks=[executor.shutdown],
        )

    # --------------------------------------------------
    # Tools
    # --------------------------------------------------

    def _build_tools(
        self,
        confirm: Confirm,
    ) -> tuple[ToolExecutor, list[dict]]:

        registry = ToolRegistry()
        AssistantTools().register_tools(registry)

        executor = ToolExecutor(
            registry=registry,
            permission_manager=PermissionManager(
                security_policy=SecurityPolicy(),
                confirm=confirm,
            ),
            timeout_seconds=self.settings.tool_timeout,
            rate_limiter=RateLimiter(
                max_calls=TOOL_CALLS_PER_MINUTE,
                window_seconds=60,
            ),
        )

        return executor, build_tool_definitions()

    # --------------------------------------------------
    # Memory
    # --------------------------------------------------

    def _build_memory(
        self,
        confirm: Confirm,
    ) -> _MemorySystem:

        directory = self.settings.memory_directory

        # The store and the retriever must share one embedding
        # service, or stored and query vectors differ in size.
        embedding_service = OpenAIEmbeddingService(settings=self.settings)

        store = ChromaMemoryStore(
            persist_directory=directory,
            collection_name="assistant_memories",
            embedding_service=embedding_service,
        )

        retriever = ChromaRetriever(
            collection=store.collection,
            embedding_service=embedding_service,
        )

        # Every memory change is logged, counted, and audited.
        metrics = MemoryMetrics()

        events = MemoryEventPublisher(
            [
                MemoryLoggingListener(),
                MemoryMetricsListener(metrics),
                MemoryAuditListener(
                    ChromaMemoryAuditStore(
                        persist_directory=directory,
                        collection_name="assistant_memory_audit",
                    )
                ),
            ]
        )

        manager = MemoryManager(
            store=store,
            retriever=retriever,
            # The AI decides how new memories relate to old ones;
            # the rules take over if OpenAI is down or answers
            # with something invalid.
            resolver=ResilientMemoryResolver(
                ai_resolver=AIMemoryResolver(settings=self.settings),
                fallback_resolver=MemoryResolver(),
            ),
            history_store=ChromaMemoryHistoryStore(
                persist_directory=directory,
                collection_name="assistant_memory_history",
            ),
            policy=MemoryPolicy(),
            confirmation=CallbackMemoryConfirmation(confirm),
            candidate_retriever=ScoredCandidateRetriever(retriever),
            candidate_ranker=MemoryCandidateRanker(),
            event_publisher=events,
        )

        return _MemorySystem(manager=manager, store=store, metrics=metrics)

    # --------------------------------------------------
    # Health checks
    # --------------------------------------------------

    @staticmethod
    def _check_microphone(
        speech: SpeechService,
    ) -> HealthCheckResult:

        if speech.health_check():
            return HealthCheckResult(
                name="microphone",
                healthy=True,
                message="Microphone is available.",
            )

        return HealthCheckResult(
            name="microphone",
            healthy=False,
            message="Microphone is unavailable.",
        )

    @staticmethod
    def _check_memory_store(
        memory_store: ChromaMemoryStore,
    ) -> HealthCheckResult:

        try:
            count = memory_store.collection.count()

        except Exception as error:
            return HealthCheckResult(
                name="memory",
                healthy=False,
                message=f"Memory store is unavailable: {error}",
            )

        return HealthCheckResult(
            name="memory",
            healthy=True,
            message=f"Memory store is available ({count} memories).",
        )
