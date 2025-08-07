from typing import Protocol, TypeVar, Generic, ContextManager
import abc

T_Conn = TypeVar("T_Conn")

class IConnection(Protocol):
    """Represents a single, generic connection."""
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def is_active(self) -> bool: ...

class IConnectionPool(Protocol, Generic[T_Conn]):
    """
    Manages a pool of connections.
    """
    @abc.abstractmethod
    def get_connection(self) -> ContextManager[T_Conn]:
        """
        A context manager that provides a connection from the pool.
        The connection is automatically returned upon exiting the context.
        """
        ...

    def shutdown(self) -> None:
        """
        Closes all connections in the pool.
        """
        ...

class IRetryPolicy(Protocol):
    """
    Defines a policy for retrying an operation that might fail.
    """
    def execute(self, action: callable, *args, **kwargs) -> Any:
        """
        Executes an action, retrying it according to the policy if it fails.

        Args:
            action: The callable to execute.
            *args: Positional arguments for the action.
            **kwargs: Keyword arguments for the action.

        Returns:
            The result of the action if it succeeds.

        Raises:
            Exception: If the action fails after all retry attempts.
        """
        ...

class ICircuitBreaker(Protocol):
    """
    Implements the circuit breaker pattern to prevent repeated calls to a failing service.
    """
    @abc.abstractmethod
    def call(self, action: callable, *args, **kwargs) -> Any:
        """
        Calls an action through the circuit breaker.

        If the circuit is closed, the action is executed.
        If the circuit is open, the action is rejected immediately.

        Args:
            action: The callable to execute.
            *args: Positional arguments for the action.
            **kwargs: Keyword arguments for the action.

        Returns:
            The result of the action if it succeeds.

        Raises:
            CircuitBreakerOpenError: If the circuit is open.
            Exception: The exception from the action if it fails.
        """
        ...

    def is_open(self) -> bool: ...
