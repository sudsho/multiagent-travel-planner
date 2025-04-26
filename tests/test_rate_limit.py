import time

from src.rate_limit import TokenBucket


def test_acquire_within_capacity():
    b = TokenBucket(rate_per_minute=600, capacity=10)
    for _ in range(5):
        assert b.acquire(1) is True


def test_non_blocking_returns_false_when_empty():
    b = TokenBucket(rate_per_minute=600, capacity=2)
    assert b.acquire(1, block=False) is True
    assert b.acquire(1, block=False) is True
    assert b.acquire(1, block=False) is False


def test_refill_over_time():
    b = TokenBucket(rate_per_minute=600, capacity=2)  # 10/sec
    b.acquire(2, block=False)
    time.sleep(0.4)
    assert b.acquire(1, block=False) is True
