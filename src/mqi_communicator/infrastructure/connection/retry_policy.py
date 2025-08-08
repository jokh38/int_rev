import time
from typing import Callable, Any, Tuple

class RetryPolicy:
    """
    Implements a retry mechanism with exponential backoff.
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, exponential_base: float = 2.0, retry_on: Tuple[type[Exception], ...] = (Exception,)):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on = retry_on

    def execute(self, action: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Executes the given action, retrying on failure.
        """
        last_exception = None
        for attempt in range(self.max_attempts):
            try:
                return action(*args, **kwargs)
            except self.retry_on as e:
                last_exception = e
                if attempt == self.max_attempts - 1:
                    break # Don't sleep on the last attempt

                delay = self.base_delay * (self.exponential_base ** attempt)
                sleep_time = min(delay, self.max_delay)

                # Add some jitter to avoid thundering herd problem
                jitter = sleep_time * 0.1
                time.sleep(sleep_time + jitter)

        raise last_exception
