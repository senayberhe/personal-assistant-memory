from assistant.application import Application
from assistant.factory import ApplicationFactory


def test_factory_creates_application(settings):

    factory = ApplicationFactory(
        settings=settings
    )

    application = factory.create()

    assert isinstance(
        application,
        Application,
    )


def test_factory_wires_history_and_health_checks(settings, tmp_path):

    application = ApplicationFactory(settings=settings).create()

    memory_manager = application.assistant.agent.memory_manager

    assert memory_manager.history_store is not None
    assert memory_manager.store.embedding_service is not None
    assert (tmp_path / "chroma.sqlite3").exists()

    results = {
        result.name: result
        for result in application.health_checker.run()
    }

    assert results["memory"].healthy


def test_factory_uses_ai_memory_resolver(settings):
    from assistant.memory.confirmation import CallbackMemoryConfirmation
    from assistant.memory.policy import MemoryPolicy
    from assistant.memory.resolution.ai import AIMemoryResolver
    from assistant.memory.resolution.resilient import ResilientMemoryResolver
    from assistant.memory.resolution.rules import MemoryResolver
    from assistant.memory.retrieval.scored_candidate_retriever import (
        ScoredCandidateRetriever,
    )


    application = ApplicationFactory(settings=settings).create()

    manager = application.assistant.agent.memory_manager

    assert isinstance(manager.resolver, ResilientMemoryResolver)
    assert isinstance(manager.resolver.ai_resolver, AIMemoryResolver)
    assert isinstance(manager.resolver.fallback_resolver, MemoryResolver)
    assert isinstance(
        manager.candidate_retriever,
        ScoredCandidateRetriever,
    )
    assert manager.store.embedding_service is not None
    assert isinstance(manager.policy, MemoryPolicy)
    assert isinstance(manager.confirmation, CallbackMemoryConfirmation)


def test_text_interface_builds_chat_without_microphone(settings):
    from io import StringIO

    from rich.console import Console

    from assistant.agent import TEXT_INSTRUCTIONS
    from assistant.interfaces.text_chat import TextChat

    console = Console(file=StringIO())

    application = ApplicationFactory(settings=settings).create(
        interface="text",
        console=console,
    )

    assert isinstance(application.assistant, TextChat)
    assert application.assistant.agent.instructions == TEXT_INSTRUCTIONS

    # Only the memory check: text mode must not need a microphone.
    names = [result.name for result in application.health_checker.run()]
    assert names == ["memory"]


def test_safety_features_are_wired(settings):
    application = ApplicationFactory(settings=settings).create()

    agent = application.assistant.agent
    executor = agent.executor

    assert executor.timeout_seconds == settings.tool_timeout
    assert executor.rate_limiter is not None
    assert agent.memory_manager.content_guard is not None
    assert len(agent.memory_manager.event_publisher.listeners) == 3

    application.shutdown()

