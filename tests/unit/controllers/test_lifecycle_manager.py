import pytest
import os
import signal
from unittest.mock import MagicMock, patch, mock_open

# Target for testing
from mqi_communicator.controllers.lifecycle_manager import LifecycleManager

@pytest.fixture
def pid_file(tmp_path):
    return tmp_path / "test.pid"

class TestLifecycleManager:
    @patch('os.getpid', return_value=12345)
    def test_acquire_lock_success(self, mock_getpid, pid_file):
        # Given
        manager = LifecycleManager(pid_file)

        # When
        # Use mock_open to simulate file operations
        with patch('builtins.open', mock_open()) as mock_file:
            locked = manager.acquire_lock()

            # Then
            assert locked is True
            mock_file().write.assert_called_once_with("12345")

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data="54321"))
    @patch('psutil.pid_exists', return_value=True)
    def test_acquire_lock_failure_if_already_running(self, mock_pid_exists, mock_path_exists, pid_file):
        # Given
        manager = LifecycleManager(pid_file)

        # When
        locked = manager.acquire_lock()

        # Then
        assert locked is False

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data="54321"))
    @patch('psutil.pid_exists', return_value=False) # Stale PID file
    @patch('os.getpid', return_value=12345)
    @patch('os.remove')
    def test_acquire_lock_succeeds_if_pid_is_stale(self, mock_remove, mock_getpid, mock_pid_exists, mock_path_exists, pid_file):
        # Given
        manager = LifecycleManager(pid_file)

        # When
        # We need to mock open again here for the write call
        with patch('builtins.open', mock_open()) as mock_file_write:
            locked = manager.acquire_lock()

            # Then
            assert locked is True
            # Check that the stale PID file was removed
            mock_remove.assert_called_once_with(pid_file)
            # Check that the new PID was written
            mock_file_write().write.assert_called_once_with("12345")

    @patch('os.remove')
    def test_release_lock(self, mock_remove, pid_file):
        # Given
        manager = LifecycleManager(pid_file)
        # Assume lock was acquired
        manager._locked = True

        # When
        manager.release_lock()

        # Then
        mock_remove.assert_called_once_with(pid_file)
        assert not manager._locked

    @patch('signal.signal')
    def test_register_shutdown_handler(self, mock_signal, pid_file):
        # Given
        manager = LifecycleManager(pid_file)
        handler = MagicMock()

        # When
        manager.register_shutdown_handler(handler)

        # Then
        # Check that signal.signal was called for SIGINT and SIGTERM
        mock_signal.assert_any_call(signal.SIGINT, manager._signal_handler)
        mock_signal.assert_any_call(signal.SIGTERM, manager._signal_handler)

        # Test that the handler is called when the signal handler is invoked
        manager._signal_handler(signal.SIGTERM, None)
        handler.assert_called_once()
