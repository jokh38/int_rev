import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Domain models and repository interfaces
from mqi_communicator.domain.models import Case, CaseStatus
from mqi_communicator.domain.repositories.interfaces import ICaseRepository

# Target for testing
from mqi_communicator.services.case_service import CaseService

@pytest.fixture
def mock_case_repo():
    repo = MagicMock(spec=ICaseRepository)
    # Simulate some existing cases in the repo
    repo.get_all_case_ids.return_value = ["case_001", "case_002"]
    return repo

@pytest.fixture
def mock_file_system():
    fs = MagicMock()
    # Simulate some directories found on the file system
    fs.list_directories.return_value = ["case_001", "case_002", "case_003_new"]
    return fs

@pytest.fixture
def case_service(mock_case_repo, mock_file_system) -> CaseService:
    # The service takes the repository and a file system abstraction
    return CaseService(
        case_repository=mock_case_repo,
        file_system=mock_file_system,
        scan_path="/fake/scan/path"
    )

class TestCaseService:
    def test_scan_for_new_cases(self, case_service: CaseService, mock_case_repo, mock_file_system):
        # When
        new_cases = case_service.scan_for_new_cases()

        # Then
        mock_file_system.list_directories.assert_called_once_with("/fake/scan/path")
        assert new_cases == ["case_003_new"]

        # Check that the new case was saved to the repository
        # We can inspect the calls to mock_case_repo.save
        # This is a bit more complex, we'd check that save was called with a Case object
        # with case_id = "case_003_new"
        assert mock_case_repo.save.call_count == 1
        saved_case_arg = mock_case_repo.save.call_args[0][0]
        assert isinstance(saved_case_arg, Case)
        assert saved_case_arg.case_id == "case_003_new"
        assert saved_case_arg.status == CaseStatus.NEW

    def test_scan_no_new_cases(self, case_service: CaseService, mock_case_repo, mock_file_system):
        # Given
        # The file system returns no new directories
        mock_file_system.list_directories.return_value = ["case_001", "case_002"]

        # When
        new_cases = case_service.scan_for_new_cases()

        # Then
        assert new_cases == []
        mock_case_repo.save.assert_not_called()

    def test_update_case_status(self, case_service: CaseService, mock_case_repo):
        # Given
        # A case that will be updated
        sample_case = Case(
            case_id="case001",
            status=CaseStatus.NEW,
            beam_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_case_repo.get.return_value = sample_case

        # When
        case_service.update_case_status("case001", CaseStatus.QUEUED)

        # Then
        mock_case_repo.get.assert_called_once_with("case001")
        # Check that save was called with the updated case
        saved_case_arg = mock_case_repo.save.call_args[0][0]
        assert saved_case_arg.status == CaseStatus.QUEUED

    def test_update_status_of_non_existent_case(self, case_service: CaseService, mock_case_repo):
        # Given
        mock_case_repo.get.return_value = None

        # When / Then
        # The service should probably log an error, but not raise an exception
        # This is a design decision. For now, we'll just check that save is not called.
        case_service.update_case_status("non_existent", CaseStatus.QUEUED)
        mock_case_repo.save.assert_not_called()
