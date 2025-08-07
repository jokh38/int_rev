import pytest
from unittest.mock import MagicMock, patch

# Targets for testing
from mqi_communicator.infrastructure.executors.local_executor import LocalExecutor
from mqi_communicator.infrastructure.executors.remote_executor import RemoteExecutor
from mqi_communicator.infrastructure.executors.interfaces import ExecutionResult
from mqi_communicator.exceptions import ExecutorError

class TestLocalExecutor:
    def test_execute_success(self):
        # Given
        executor = LocalExecutor()
        command = "echo 'hello world'"

        # When
        result = executor.execute(command)

        # Then
        assert result.succeeded()
        assert result.return_code == 0
        assert result.stdout.strip() == "hello world"
        assert result.stderr == ""

    def test_execute_failure(self):
        # Given
        executor = LocalExecutor()
        # A command that will fail
        command = "ls /non_existent_directory_12345"

        # When
        result = executor.execute(command)

        # Then
        assert not result.succeeded()
        assert result.return_code != 0
        assert result.stdout == ""
        assert "No such file or directory" in result.stderr

    def test_execute_timeout(self):
        # Given
        executor = LocalExecutor()
        command = "sleep 2"

        # When / Then
        with pytest.raises(TimeoutError):
            executor.execute(command, timeout=1)

class TestRemoteExecutor:
    @pytest.fixture
    def mock_ssh_client(self):
        mock_client = MagicMock()
        # Mock the exec_command to return mock stdin, stdout, stderr
        mock_stdin, mock_stdout, mock_stderr = MagicMock(), MagicMock(), MagicMock()
        mock_stdout.read.return_value = b"remote output"
        mock_stderr.read.return_value = b"remote error"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        return mock_client

    @pytest.fixture
    def mock_connection_pool(self, mock_ssh_client):
        mock_pool = MagicMock()
        # Make the context manager yield the mock client
        mock_pool.get_connection.return_value.__enter__.return_value = mock_ssh_client
        return mock_pool

    def test_execute_success(self, mock_connection_pool, mock_ssh_client):
        # Given
        executor = RemoteExecutor(mock_connection_pool)
        command = "cat /remote/file"

        # When
        result = executor.execute(command)

        # Then
        mock_ssh_client.exec_command.assert_called_once_with(command, timeout=None)
        assert result.succeeded()
        assert result.stdout.strip() == "remote output"
        assert result.stderr.strip() == "remote error"
        assert result.return_code == 0

    def test_execute_failure(self, mock_connection_pool, mock_ssh_client):
        # Given
        # Configure the mock to return a non-zero exit code
        mock_stdout = mock_ssh_client.exec_command.return_value[1]
        mock_stdout.channel.recv_exit_status.return_value = 127

        executor = RemoteExecutor(mock_connection_pool)
        command = "bad_command"

        # When
        result = executor.execute(command)

        # Then
        assert not result.succeeded()
        assert result.return_code == 127

    def test_execute_raises_executor_error_on_ssh_exception(self, mock_connection_pool, mock_ssh_client):
        # Given
        mock_ssh_client.exec_command.side_effect = Exception("SSH connection failed")
        executor = RemoteExecutor(mock_connection_pool)

        # When / Then
        with pytest.raises(ExecutorError, match="Failed to execute remote command"):
            executor.execute("some command")
