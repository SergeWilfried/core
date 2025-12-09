"""
Retry logic for external API calls
"""

import asyncio
from typing import TypeVar, Callable, Optional, Type
from functools import wraps
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..exceptions import FormanceAPIError, ExternalServiceError


logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_api_error(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    exceptions: tuple[Type[Exception], ...] = (FormanceAPIError, ExternalServiceError),
):
    """
    Retry decorator for API calls with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exceptions to retry on
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


async def retry_async(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> T:
    """
    Manually retry an async function with exponential backoff

    Args:
        func: Async function to retry
        max_attempts: Maximum retry attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        exceptions: Exceptions to catch and retry

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    current_delay = delay
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                    f"Retrying in {current_delay}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    f"All {max_attempts} attempts failed. Last error: {e}"
                )

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed without exception")


def with_retry(max_attempts: int = 3):
    """
    Decorator to add retry logic to async functions

    Usage:
        @with_retry(max_attempts=3)
        async def my_function():
            # function code
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
            )
        return wrapper
    return decorator
