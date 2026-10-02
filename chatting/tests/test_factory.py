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
    from assistant.memory.confirmation import ConsoleMemoryConfirmation
    from assistant.memory.policy import MemoryPolicy
    from assistant.memory.resolution.ai import AIMemoryResolver
    from assistant.memory.resolution.resilient import ResilientMemoryResolver
    from assistant.memory.resolution.rules import MemoryResolver
    from assistant.memory.retrieval.chroma_candidate_retriever import (
        ChromaMemoryCandidateRetriever,
    )


    application = ApplicationFactory(settings=settings).create()

    manager = application.assistant.agent.memory_manager

    assert isinstance(manager.resolver, ResilientMemoryResolver)
    assert isinstance(manager.resolver.ai_resolver, AIMemoryResolver)
    assert isinstance(manager.resolver.fallback_resolver, MemoryResolver)
    assert isinstance(
        manager.candidate_retriever,
        ChromaMemoryCandidateRetriever,
    )
    assert manager.store.embedding_service is not None
    assert isinstance(manager.policy, MemoryPolicy)
    assert isinstance(manager.confirmation, ConsoleMemoryConfirmation)

