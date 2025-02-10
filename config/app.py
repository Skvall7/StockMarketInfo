import logging
import time
from functools import wraps

from faststream import FastStream
from faststream.confluent import KafkaBroker

from config.config import settings

logger = logging.getLogger(settings.title)

broker = KafkaBroker(settings.kafka_connections, log_level=logging.DEBUG, logger=logger)

app = FastStream(
    broker,
    title=settings.title,
    version=settings.version,
    description=settings.description
)


def log_execution_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.debug(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper
