import pytest
from unittest.mock import MagicMock

# Infrastructure interfaces
from mqi_communicator.infrastructure.executors.interfaces import IExecutor, ExecutionResult

# Target for testing
from mqi_communicator.services.transfer_service import TransferService

@pytest.fixture
def mock_remote_executor():
    executor = MagicMock(spec=IExecutor)
    executor.execute.return_value = ExecutionResult(stdout="", stderr="", return_code=0)
    return executor

@pytest.fixture
def transfer_service(mock_remote_executor) -> TransferService:
    # Service depends on an executor and some path configurations
    return TransferService(
        remote_executor=mock_remote_executor,
        local_data_path="/local/data",
        remote_workspace_path="/remote/workspace"
    )

class TestTransferService:
    def test_upload_case(self, transfer_service: TransferService, mock_remote_executor):
        # Given
        case_id = "case_to_upload"

        # When
        transfer_service.upload_case(case_id)

        # Then
        # Verify that the executor was called with the correct scp/rsync command
        # The exact command depends on the implementation choice (e.g., rsync, scp)
        # Let's assume rsync for its efficiency.
        expected_command = (
            "rsync -az -e 'ssh' "
            f"/local/data/{case_id} "
            f"user@host:/remote/workspace/"
        )
        # The test needs to be more robust to handle different ssh configs.
        # For now, let's just check for the key parts of the command.

        called_command = mock_remote_executor.execute.call_args[0][0]
        assert f"/local/data/{case_id}" in called_command
        assert f"/remote/workspace" in called_command
        assert "rsync" in called_command

    def test_download_results(self, transfer_service: TransferService, mock_remote_executor):
        # Given
        case_id = "case_to_download"

        # When
        transfer_service.download_results(case_id)

        # Then
        # Verify the download command
        expected_command = (
            "rsync -az -e 'ssh' "
            f"user@host:/remote/workspace/{case_id}/results/ "
            f"/local/data/{case_id}/"
        )

        called_command = mock_remote_executor.execute.call_args[0][0]
        assert f"/remote/workspace/{case_id}" in called_command
        assert f"/local/data/{case_id}" in called_command
        assert "rsync" in called_command

    def test_upload_fails_on_executor_error(self, transfer_service: TransferService, mock_remote_executor):
        # Given
        # The executor will return a failed result
        mock_remote_executor.execute.return_value = ExecutionResult(
            stdout="", stderr="permission denied", return_code=1
        )

        # When / Then
        # The service should raise an exception if the transfer fails
        with pytest.raises(Exception, match="Failed to upload case"):
            transfer_service.upload_case("case_abc")
