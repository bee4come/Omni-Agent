"""
Tests for retry utilities.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
import time

from utils.retry import (
    retry_with_backoff,
    RetryConfig,
    calculate_delay,
    should_retry,
    with_retry,
    RetryableHTTPClient
)


class TestRetryConfig:
    """Test RetryConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            jitter=False
        )
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.jitter is False


class TestCalculateDelay:
    """Test delay calculation."""

    def test_exponential_backoff(self):
        """Test that delay increases exponentially."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)

        delay_0 = calculate_delay(0, config)
        delay_1 = calculate_delay(1, config)
        delay_2 = calculate_delay(2, config)

        assert delay_0 == 1.0
        assert delay_1 == 2.0
        assert delay_2 == 4.0

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=10.0, max_delay=15.0, jitter=False)

        delay = calculate_delay(5, config)  # Would be 320 without cap
        assert delay == 15.0

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(base_delay=1.0, jitter=True, jitter_factor=0.5)

        # Calculate multiple delays and verify they're different
        delays = [calculate_delay(0, config) for _ in range(10)]

        # With jitter, delays should vary
        unique_delays = set(delays)
        assert len(unique_delays) > 1  # Should have some variation


class TestShouldRetry:
    """Test retry decision logic."""

    def test_should_not_retry_on_max_attempts(self):
        """Test that we don't retry after max attempts."""
        config = RetryConfig(max_retries=3)

        result = should_retry(ConnectionError(), 3, config)
        assert result is False

    def test_should_retry_connection_error(self):
        """Test that ConnectionError triggers retry."""
        config = RetryConfig()

        result = should_retry(ConnectionError(), 0, config)
        assert result is True

    def test_should_retry_timeout_error(self):
        """Test that TimeoutError triggers retry."""
        config = RetryConfig()

        result = should_retry(TimeoutError(), 0, config)
        assert result is True

    def test_should_not_retry_value_error(self):
        """Test that ValueError does not trigger retry."""
        config = RetryConfig()

        result = should_retry(ValueError(), 0, config)
        assert result is False


class TestRetryDecorator:
    """Test retry_with_backoff decorator."""

    def test_success_on_first_try(self):
        """Test that successful call works without retry."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = always_succeeds()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_connection_error(self):
        """Test retry on ConnectionError."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count == 3

    def test_max_retries_exhausted(self):
        """Test that exception is raised after max retries."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            always_fails()

        assert call_count == 3  # 1 initial + 2 retries

    def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are raised immediately."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Bad value")

        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count == 1  # No retries

    def test_on_retry_callback(self):
        """Test that on_retry callback is called."""
        retry_calls = []

        def on_retry(exc, attempt):
            retry_calls.append((type(exc).__name__, attempt))

        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01, on_retry=on_retry)
        def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Fail")
            return "success"

        result = fails_once()
        assert result == "success"
        assert len(retry_calls) == 1
        assert retry_calls[0] == ("ConnectionError", 0)


class TestAsyncRetry:
    """Test async function retry."""

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test retry with async function."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def async_fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Async connection failed")
            return "async success"

        result = await async_fails_twice()
        assert result == "async success"
        assert call_count == 3


class TestWithRetry:
    """Test with_retry convenience function."""

    def test_with_retry_success(self):
        """Test with_retry on successful function."""
        def add(a, b):
            return a + b

        result = with_retry(add, 1, 2, max_retries=3)
        assert result == 3

    def test_with_retry_fails_then_succeeds(self):
        """Test with_retry with transient failure."""
        call_count = 0

        def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Fail once")
            return "recovered"

        result = with_retry(fails_once, max_retries=3, base_delay=0.01)
        assert result == "recovered"
        assert call_count == 2


class TestDecoratorUsageStyles:
    """Test different decorator usage styles."""

    def test_decorator_without_parens(self):
        """Test @retry_with_backoff without parentheses."""
        call_count = 0

        @retry_with_backoff
        def simple_func():
            nonlocal call_count
            call_count += 1
            return "done"

        result = simple_func()
        assert result == "done"
        assert call_count == 1

    def test_decorator_with_config(self):
        """Test @retry_with_backoff with RetryConfig."""
        config = RetryConfig(max_retries=1, base_delay=0.01)
        call_count = 0

        @retry_with_backoff(config=config)
        def configured_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Fail")
            return "done"

        result = configured_func()
        assert result == "done"
        assert call_count == 2
