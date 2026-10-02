from assistant.memory.events.metrics import MemoryMetrics


def test_contradiction_counts_as_update_and_contradiction():
    metrics = MemoryMetrics()

    metrics.record("update", success=True, resolution="contradict")
    metrics.record("update", success=True, resolution="update")
    metrics.record("create", success=True)
    metrics.record("create", success=False)

    assert metrics.snapshot() == {
        "created": 1,
        "updated": 2,
        "ignored": 0,
        "contradicted": 1,
        "failed": 1,
    }
