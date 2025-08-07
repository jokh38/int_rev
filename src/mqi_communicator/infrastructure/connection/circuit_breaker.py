import time
from typing import Callable, Any

class CircuitBreakerOpenError(Exception):
    """Exception raised when a circuit breaker is open."""
    pass

class CircuitBreaker:
    """
    Implements the Circuit Breaker pattern.
    """

    _STATE_CLOSED = "closed"
    _STATE_OPEN = "open"
    _STATE_HALF_OPEN = "half-open"

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time: float | None = None
        self.state = self._STATE_CLOSED

    def is_open(self) -> bool:
        """Check if the circuit is currently open."""
        if self.state == self._STATE_OPEN:
            # Check if the timeout has passed, if so, move to half-open
            if time.time() > self.last_failure_time + self.timeout:
                self.state = self._STATE_HALF_OPEN
                return False # Allow the next call
            return True
        return False

    def call(self, action: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Executes the action, respecting the circuit breaker's state.
        """
        if self.is_open():
            raise CircuitBreakerOpenError("Circuit breaker is open.")

        try:
            result = action(*args, **kwargs)
            # If the call was successful, reset the breaker
            self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def _record_failure(self):
        """Records a failure and opens the circuit if the threshold is met."""
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = self._STATE_OPEN
            self.last_failure_time = time.time()

    def _reset(self):
        """Resets the circuit breaker to the closed state."""
        self.state = self._STATE_CLOSED
        self.failures = 0
        self.last_failure_time = None
