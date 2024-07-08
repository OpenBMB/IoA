from common.log import logger
from tenacity import RetryCallState


def log_retry(retry_state: RetryCallState):
    exception = retry_state.outcome.exception()
    logger.warn(
        f"Retrying {retry_state.fn}\nAttempt: {retry_state.attempt_number}\nException: {exception.__class__.__name__} {exception}",
    )
