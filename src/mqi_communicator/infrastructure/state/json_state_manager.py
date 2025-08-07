import json
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Any, ContextManager
import copy
import os

from .interfaces import IStateManager, ITransactionContext

class JsonStateManager(IStateManager):
    """
    A thread-safe, transactional state manager that persists state to a JSON file.
    It ensures atomic writes to prevent data corruption.
    """

    def __init__(self, state_file: Path):
        self._state_file = state_file
        self._lock = threading.RLock()
        self._state: dict[str, Any] = {}
        self._load_state()

    def _load_state(self):
        with self._lock:
            if self._state_file.exists():
                with self._state_file.open("r") as f:
                    try:
                        self._state = json.load(f)
                    except json.JSONDecodeError:
                        # Handle case of empty or corrupted file
                        self._state = {}
            else:
                self._state = {}
                self._persist()

    def _persist(self):
        """
        Atomically persists the current in-memory state to the JSON file.
        Writes to a temporary file first, then renames it to the final destination.
        """
        with self._lock:
            temp_file_path = self._state_file.with_suffix(f"{self._state_file.suffix}.tmp")
            with temp_file_path.open("w") as f:
                json.dump(self._state, f, indent=2)
            os.rename(temp_file_path, self._state_file)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return copy.deepcopy(self._state.get(key, default))

    def set(self, key: str, value: Any):
        with self._lock:
            self._state[key] = value
            self._persist()

    @contextmanager
    def transaction(self) -> ContextManager[ITransactionContext]:
        """
        Provides a transactional context for state modifications.
        """
        with self._lock:
            # The transaction operates on a deep copy of the state.
            temp_state = copy.deepcopy(self._state)

            class TransactionContext(ITransactionContext):
                def get_state(self) -> dict[str, Any]:
                    return temp_state

            try:
                yield TransactionContext()
                # If the context exits without error, commit the changes.
                self._state = temp_state
                self._persist()
            except Exception:
                # If an error occurred, the changes to temp_state are discarded
                # and the original self._state is preserved.
                raise
