from aiohttp.client_exceptions import ClientResponseError
from functools import wraps
import logging
import asyncio

logger = logging.getLogger(__name__)

def retry_on_429(func=None, *, max_retries=10, initial_delay=1):
    if func and callable(func):
        return retry_on_429(max_retries=max_retries, initial_delay=initial_delay)(func)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except ClientResponseError as e:
                    if e.status == 429:
                        logger.warning(f"429 encountered, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        raise
            raise Exception("Max retries reached")
        return wrapper

    return decorator