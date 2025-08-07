from typing import Protocol, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager
import abc

T = TypeVar('T')

class ITransactionContext(Protocol):
    """
    An interface for a transaction context that allows getting and setting state
    within a transaction.
    """
    def get_state(self) -> dict[str, Any]:
        """
        Returns a mutable copy of the current state for modification within the transaction.
        """
        ...

class IStateManager(Protocol):
    """
    An interface for a thread-safe, transactional state manager.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value from the state by key.

        Args:
            key: The key of the value to retrieve.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value.
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the state. This operation should be atomic.

        Args:
            key: The key of the value to set.
            value: The value to set.
        """
        ...

    @abc.abstractmethod
    def transaction(self) -> ContextManager[ITransactionContext]:
        """
        Provides a transactional context for state modifications.
        Changes are only persisted if the context exits without an exception.
        """
        ...
