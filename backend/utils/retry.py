"""
Retry utilities with exponential backoff for error recovery.

Usage:
    from utils.retry import retry_with_backoff, RetryConfig

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def my_function():
        ...

    # With custom config
    config = RetryConfig(max_retries=5, base_delay=0.5, max_delay=30.0)
    @retry_with_backoff(config=config)
    async def my_async_function():
        ...
"""
import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Set, Type, Union, Any

logger = logging.getLogger(__name__)


# Common transient errors that should trigger retry
TRANSIENT_EXCEPTIONS: Set[Type[Exception]] = {
    ConnectionError,
    TimeoutError,
    ConnectionResetError,
    ConnectionRefusedError,
}

# Try to add httpx exceptions if available
try:
    import httpx
    TRANSIENT_EXCEPTIONS.add(httpx.TransportError)
    TRANSIENT_EXCEPTIONS.add(httpx.TimeoutException)
    TRANSIENT_EXCEPTIONS.add(httpx.ConnectError)
except ImportError:
    pass


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.5  # 0.5 = +/- 50%
    retryable_exceptions: Set[Type[Exception]] = field(
        default_factory=lambda: TRANSIENT_EXCEPTIONS.copy()
    )


def calculate_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate delay before next retry attempt with exponential backoff.

    Args:
        attempt: Current attempt number (0-based)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    delay = min(
        config.base_delay * (config.exponential_base ** attempt),
        config.max_delay
    )

    if config.jitter:
        jitter_range = delay * config.jitter_factor
        delay = delay + random.uniform(-jitter_range, jitter_range)

    return max(0.0, delay)


def should_retry(
    exception: Exception,
    attempt: int,
    config: RetryConfig
) -> bool:
    """
    Determine if we should retry based on the exception and attempt count.

    Args:
        exception: The caught exception
        attempt: Current attempt number (0-based)
        config: Retry configuration

    Returns:
        True if should retry, False otherwise
    """
    if attempt >= config.max_retries:
        return False

    # Check if exception type is retryable
    for exc_type in config.retryable_exceptions:
        if isinstance(exception, exc_type):
            return True

    # Check for nested exceptions (e.g., httpx wrapping connection errors)
    if hasattr(exception, '__cause__') and exception.__cause__:
        for exc_type in config.retryable_exceptions:
            if isinstance(exception.__cause__, exc_type):
                return True

    return False


def retry_with_backoff(
    func: Optional[Callable] = None,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator that adds retry logic with exponential backoff.

    Can be used with or without parameters:
        @retry_with_backoff
        def my_func(): ...

        @retry_with_backoff(max_retries=5)
        def my_func(): ...

        @retry_with_backoff(config=my_config)
        def my_func(): ...

    Args:
        func: The function to wrap (for no-argument decorator usage)
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        config: Optional RetryConfig to override individual parameters
        on_retry: Optional callback called on each retry with (exception, attempt)

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter
        )

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not should_retry(e, attempt, config):
                        raise

                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"[RETRY] {fn.__name__} attempt {attempt + 1}/{config.max_retries + 1} "
                        f"failed with {type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not should_retry(e, attempt, config):
                        raise

                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"[RETRY] {fn.__name__} attempt {attempt + 1}/{config.max_retries + 1} "
                        f"failed with {type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    await asyncio.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    # Handle both @retry_with_backoff and @retry_with_backoff() usage
    if func is not None:
        return decorator(func)
    return decorator


class RetryableHTTPClient:
    """
    HTTP client wrapper with built-in retry logic.

    Usage:
        client = RetryableHTTPClient(max_retries=3)
        response = client.get("http://example.com/api")
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        timeout: float = 30.0,
        config: Optional[RetryConfig] = None
    ):
        self.config = config or RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay
        )
        self.timeout = timeout

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Any:
        """Make an HTTP request with retry logic."""
        import httpx

        kwargs.setdefault('timeout', self.timeout)

        @retry_with_backoff(config=self.config)
        def _request():
            with httpx.Client() as client:
                response = getattr(client, method.lower())(url, **kwargs)
                # Raise for 5xx errors (server errors are retryable)
                if 500 <= response.status_code < 600:
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response
                    )
                return response

        return _request()

    def get(self, url: str, **kwargs) -> Any:
        """HTTP GET with retry."""
        return self._make_request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Any:
        """HTTP POST with retry."""
        return self._make_request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Any:
        """HTTP PUT with retry."""
        return self._make_request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        """HTTP DELETE with retry."""
        return self._make_request('DELETE', url, **kwargs)


# Convenience function for one-off retryable calls
def with_retry(
    fn: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Execute a function with retry logic.

    Usage:
        result = with_retry(my_function, arg1, arg2, max_retries=3)

    Args:
        fn: Function to execute
        *args: Positional arguments for the function
        max_retries: Maximum retry attempts
        base_delay: Initial delay between retries
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function call
    """
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)

    @retry_with_backoff(config=config)
    def wrapped():
        return fn(*args, **kwargs)

    return wrapped()
