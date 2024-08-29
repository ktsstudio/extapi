import time

from extapi.limiters.rps.local import LocalRateLimiter


class TestLocalLimiter:
    async def test_no_limit(self, rate_limit: int):
        started_at = time.monotonic()
        limiter = LocalRateLimiter(rate_limit=0)
        await limiter.rate_limit()
        assert time.monotonic() - started_at < 0.01

    async def test_a_lot_free_space(self):
        started_at = time.monotonic()
        limiter = LocalRateLimiter(rate_limit=100)
        await limiter.rate_limit()
        assert time.monotonic() - started_at < 0.01

    async def test_rate_limited(self):
        limiter = LocalRateLimiter(rate_limit=1, rate_limit_window_seconds=2)
        await limiter.rate_limit()  # no rate limit

        started_at = time.monotonic()
        await limiter.rate_limit()
        assert time.monotonic() - started_at >= 1.5
