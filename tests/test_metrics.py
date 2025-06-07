import time

from src.utils.metrics import record_latency, get_average_latency, get_sla_breaches


def test_sla_breach_recorded():
    record_latency("search", 200, sla_ms=100)
    assert get_sla_breaches("search") == 1


def test_average_latency_computation():
    record_latency("search", 100)
    record_latency("search", 300)
    avg = get_average_latency("search")
    assert 199 < avg < 201
