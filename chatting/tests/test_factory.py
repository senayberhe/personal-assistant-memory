from assistant.application import Application
from assistant.factory import ApplicationFactory
from config.settings import Settings


def test_factory_creates_application(tmp_path):

    settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        environment="testing",
        log_level="WARNING",
        api_timeout=30,
        tool_timeout=10,
        max_agent_steps=10,
        max_plan_steps=10,
        speech_timeout=5,
        phrase_time_limit=8,
        ambient_noise_duration=1,
        memory_directory=str(tmp_path),
    )

    factory = ApplicationFactory(
        settings=settings
    )

    application = factory.create()

    assert isinstance(
        application,
        Application,
    )


def test_factory_wires_history_and_health_checks(tmp_path):
    settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        environment="testing",
        log_level="WARNING",
        api_timeout=30,
        tool_timeout=10,
        max_agent_steps=10,
        max_plan_steps=10,
        speech_timeout=5,
        phrase_time_limit=8,
        ambient_noise_duration=1,
        memory_directory=str(tmp_path),
    )

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


def test_factory_uses_ai_memory_resolver(tmp_path):
    from assistant.memory.resolution.ai import AIMemoryResolver
    from assistant.memory.retrieval.chroma_candidate_retriever import (
        ChromaMemoryCandidateRetriever,
    )
    from assistant.memory.confirmation import ConsoleMemoryConfirmation
    from assistant.memory.policy import MemoryPolicy
    from assistant.memory.resolution.rules import MemoryResolver
    from assistant.memory.resolution.resilient import ResilientMemoryResolver

    settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        environment="testing",
        log_level="WARNING",
        api_timeout=30,
        tool_timeout=10,
        max_agent_steps=10,
        max_plan_steps=10,
        speech_timeout=5,
        phrase_time_limit=8,
        ambient_noise_duration=1,
        memory_directory=str(tmp_path),
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

