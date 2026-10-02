from assistant.metrics import Metrics

def test_success_metric():
    metrics = Metrics()

    metrics.record_success(
        "search_google",
        0.5,
    )

    result = metrics.get(
        "search_google"
    )

    assert result is not None
    assert result.calls == 1
    assert result.successes == 1
    assert result.failures == 0
    assert result.total_latency == 0.5
    assert result.average_latency == 0.5