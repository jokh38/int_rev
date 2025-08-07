import pytest
import json
import threading
from pathlib import Path
import time

# Target for testing
from mqi_communicator.infrastructure.state.json_state_manager import JsonStateManager

@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "state.json"

class TestJsonStateManager:
    def test_initialization_creates_file(self, state_file: Path):
        # Given the file does not exist
        assert not state_file.exists()

        # When
        manager = JsonStateManager(state_file)

        # Then
        assert state_file.exists()
        with open(state_file, "r") as f:
            assert json.load(f) == {}

    def test_initialization_loads_existing_file(self, state_file: Path):
        # Given
        initial_state = {"key1": "value1"}
        with open(state_file, "w") as f:
            json.dump(initial_state, f)

        # When
        manager = JsonStateManager(state_file)

        # Then
        assert manager.get("key1") == "value1"

    def test_get_and_set(self, state_file: Path):
        # Given
        manager = JsonStateManager(state_file)

        # When
        manager.set("name", "Jules")

        # Then
        assert manager.get("name") == "Jules"
        # Verify persistence
        with open(state_file, "r") as f:
            assert json.load(f)["name"] == "Jules"

    def test_get_with_default(self, state_file: Path):
        # Given
        manager = JsonStateManager(state_file)

        # When / Then
        assert manager.get("non_existent", "default_val") == "default_val"

    def test_transaction_success(self, state_file: Path):
        # Given
        manager = JsonStateManager(state_file)
        manager.set("counter", 0)

        # When
        with manager.transaction() as tx:
            state = tx.get_state()
            state["counter"] = 1
            state["new_key"] = "added"

        # Then
        assert manager.get("counter") == 1
        assert manager.get("new_key") == "added"

    def test_transaction_rollback_on_exception(self, state_file: Path):
        # Given
        manager = JsonStateManager(state_file)
        manager.set("status", "initial")

        # When
        with pytest.raises(ValueError, match="Something went wrong"):
            with manager.transaction() as tx:
                state = tx.get_state()
                state["status"] = "modified"
                raise ValueError("Something went wrong")

        # Then
        assert manager.get("status") == "initial"

    def test_thread_safety_with_concurrent_sets(self, state_file: Path):
        # Given
        manager = JsonStateManager(state_file)
        manager.set("counter", 0)
        num_threads = 10
        increments_per_thread = 100

        # When
        def increment():
            for _ in range(increments_per_thread):
                with manager.transaction() as tx:
                    state = tx.get_state()
                    current = state.get("counter", 0)
                    time.sleep(0.001) # Introduce a small delay to encourage race conditions
                    state["counter"] = current + 1

        threads = [threading.Thread(target=increment) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Then
        assert manager.get("counter") == num_threads * increments_per_thread

    def test_atomic_write(self, state_file: Path, monkeypatch):
        # This test ensures that if a write fails midway, the original file is preserved.
        # Given
        manager = JsonStateManager(state_file)
        manager.set("data", "original")

        # When
        original_dump = json.dump
        def failing_dump(*args, **kwargs):
            # Fail on the second write (the actual state write)
            if args[0] == {"data": "new"}:
                 raise IOError("Disk full")
            return original_dump(*args, **kwargs)

        monkeypatch.setattr(json, "dump", failing_dump)

        with pytest.raises(IOError):
            manager.set("data", "new")

        # Then
        # The file should still contain the original data
        with open(state_file, "r") as f:
            assert json.load(f) == {"data": "original"}
