from typing import Protocol, Callable

class ILifecycleManager(Protocol):
    """
    Interface for a component that manages the application lifecycle.
    """
    def acquire_lock(self) -> bool:
        """Acquires a process lock. Returns True on success."""
        ...

    def release_lock(self) -> None:
        """Releases the process lock."""
        ...

    def register_shutdown_handler(self, handler: Callable[[], None]) -> None:
        """Registers a handler to be called on graceful shutdown."""
        ...
