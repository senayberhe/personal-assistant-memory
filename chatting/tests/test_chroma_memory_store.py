from datetime import datetime, timedelta
from assistant.chroma_memory_store import ChromaMemoryStore
from assistant.memory import Memory
from tests.fakes.memory_confirmation import FakeMemoryConfirmation


def test_save_and_get_memory(tmp_path):
    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
    )

    memory = Memory(
        id="1",
        content="Test memory",
        created_at=datetime.now(),
    )

    store.save(memory)

    memories = store.get_all()
    assert len(memories) == 1
    assert memories[0].id == memory.id
    assert memories[0].content == memory.content

    retrieved = store.get("1")
    assert retrieved is not None
    assert retrieved.id == memory.id
    assert retrieved.content == memory.content


def test_delete_memory(tmp_path):
    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
    )

    memory = Memory(
        id="memory-1",
        content="User likes Python",
        created_at=datetime.now(),
        memory_type="preference"
    )

    store.save(memory)
    store.delete("memory-1")

    retrieved = store.get("memory-1")
    assert retrieved is None

    memories = store.get_all()
    assert len(memories) == 0


def test_memory_metadata_persists(tmp_path):
    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
    )

    memory = Memory(
        id="memory-2",
        content="User prefers dark mode",
        created_at=datetime.now(),
        memory_type="preference"
    )

    store.save(memory)
    memories = store.get_all()
    assert len(memories) == 1
    assert memories[0].id == memory.id
    assert memories[0].content == memory.content
    assert memories[0].memory_type == memory.memory_type

    retrieved = store.get("memory-2")
    assert retrieved is not None
    assert retrieved.id == memory.id
    assert retrieved.content == memory.content
    assert retrieved.memory_type == memory.memory_type

def test_store_and_retriever_share_embeddings(tmp_path):
    from assistant.chroma_retriever import ChromaRetriever
    from assistant.embeddings import SimpleEmbeddingService
    from assistant.memory import MemoryManager

    embeddings = SimpleEmbeddingService()

    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
        embedding_service=embeddings,
    )

    manager = MemoryManager(
        store=store,
        retriever=ChromaRetriever(
            collection=store.collection,
            embedding_service=embeddings,
        ),
    )

    manager.remember("User likes Python", memory_type="preference")
    manager.remember("User drinks tea")

    results = manager.recall_scored("User likes Python", top_k=5)

    assert results[0].memory.content == "User likes Python"
    assert results[0].score > 0.99

    preferences = manager.recall("anything", memory_type="preference")

    assert [m.content for m in preferences] == ["User likes Python"]


def test_memory_key_and_expiry_persist(tmp_path):
    from datetime import timedelta

    from assistant.embeddings import SimpleEmbeddingService

    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
        embedding_service=SimpleEmbeddingService(),
    )

    expires_at = datetime.now() + timedelta(days=7)

    store.save(
        Memory(
            id="lang",
            content="I prefer Python.",
            created_at=datetime.now(),
            memory_key="preferred_programming_language",
            expires_at=expires_at,
        )
    )

    store.save(
        Memory(
            id="other",
            content="I like tea.",
            created_at=datetime.now(),
        )
    )

    found = store.find_by_key("preferred_programming_language")

    assert [m.id for m in found] == ["lang"]
    assert found[0].expires_at == expires_at
    assert store.get("other").memory_key is None


def test_upsert_with_chroma_updates_in_place(tmp_path):
    from assistant.chroma_retriever import ChromaRetriever
    from assistant.embeddings import SimpleEmbeddingService
    from assistant.memory import MemoryManager

    embeddings = SimpleEmbeddingService()

    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
        embedding_service=embeddings,
    )

    manager = MemoryManager(
        store=store,
        retriever=ChromaRetriever(store.collection, embeddings),
        confirmation=FakeMemoryConfirmation(approved=True),
    )

    first = manager.upsert("I prefer Python.", memory_key="lang")
    second = manager.upsert("I now prefer Rust.", memory_key="lang")

    assert first.id == second.id
    assert [m.content for m in store.get_all()] == ["I now prefer Rust."]


def test_expired_memories_are_not_recalled(tmp_path):
    from assistant.chroma_retriever import ChromaRetriever
    from assistant.embeddings import SimpleEmbeddingService
    from assistant.memory import MemoryManager

    embeddings = SimpleEmbeddingService()

    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
        embedding_service=embeddings,
    )

    manager = MemoryManager(
        store=store,
        retriever=ChromaRetriever(store.collection, embeddings),
    )

    manager.remember("Permanent fact")
    temporary = manager.remember("Temporary fact", ttl_days=1)

    temporary.expires_at = datetime.now() - timedelta(seconds=1)
    store.save(temporary)

    recalled = [m.content for m in manager.recall("fact", top_k=5)]

    assert recalled == ["Permanent fact"]
    assert manager.cleanup_expired() == 1
    assert len(store.get_all()) == 1


def test_version_persists(tmp_path):
    from assistant.chroma_retriever import ChromaRetriever
    from assistant.embeddings import SimpleEmbeddingService
    from assistant.in_memory_history_store import InMemoryHistoryStore
    from assistant.memory import MemoryManager

    embeddings = SimpleEmbeddingService()

    store = ChromaMemoryStore(
        persist_directory=tmp_path,
        collection_name="test_memories",
        embedding_service=embeddings,
    )

    history = InMemoryHistoryStore()

    manager = MemoryManager(
        store=store,
        retriever=ChromaRetriever(store.collection, embeddings),
        history_store=history,
        confirmation=FakeMemoryConfirmation(approved=True),
    )

    memory = manager.upsert("I prefer Python.", memory_key="lang")
    manager.upsert("I prefer Rust.", memory_key="lang")
    manager.upsert("I prefer Go.", memory_key="lang")

    stored = store.get(memory.id)

    assert stored.version == 3
    assert stored.content == "I prefer Go."
    assert [v.content for v in history.get_history(memory.id)] == [
        "I prefer Python.",
        "I prefer Rust.",
    ]
