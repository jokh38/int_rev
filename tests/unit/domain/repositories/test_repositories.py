import pytest
from unittest.mock import MagicMock, patch
from contextlib import contextmanager
from datetime import datetime

# Domain models and repository interfaces
from mqi_communicator.domain.models import Case, CaseStatus, Job, JobStatus
from mqi_communicator.domain.repositories.interfaces import ICaseRepository, IJobRepository

# Targets for testing
from mqi_communicator.domain.repositories.json_repositories import CaseRepository, JobRepository

# Mock State Manager
@pytest.fixture
def mock_state_manager():
    mock_sm = MagicMock()
    # The state is a dictionary held by the mock
    mock_sm.state = {"cases": {}, "jobs": {}}

    # Mock the transaction context manager
    @contextmanager
    def mock_transaction():
        # The transaction operates on the same state dict for simplicity in testing
        yield mock_sm.state

    mock_sm.transaction.side_effect = mock_transaction
    return mock_sm

class TestCaseRepository:
    @pytest.fixture
    def case_repo(self, mock_state_manager) -> ICaseRepository:
        return CaseRepository(mock_state_manager)

    @pytest.fixture
    def sample_case(self) -> Case:
        return Case(
            case_id="case001",
            status=CaseStatus.NEW,
            beam_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def test_save_case(self, case_repo: ICaseRepository, mock_state_manager, sample_case: Case):
        # When
        case_repo.save(sample_case)

        # Then
        # Check that the state was modified correctly within a transaction
        mock_state_manager.transaction.assert_called_once()
        assert mock_state_manager.state["cases"]["case001"] == sample_case.model_dump()

    def test_get_case(self, case_repo: ICaseRepository, mock_state_manager, sample_case: Case):
        # Given
        mock_state_manager.state["cases"]["case001"] = sample_case.model_dump()

        # When
        retrieved_case = case_repo.get("case001")

        # Then
        assert retrieved_case is not None
        assert retrieved_case.case_id == "case001"
        assert retrieved_case.status == CaseStatus.NEW

    def test_get_non_existent_case(self, case_repo: ICaseRepository):
        # When
        retrieved_case = case_repo.get("non_existent")

        # Then
        assert retrieved_case is None

    def test_get_all_case_ids(self, case_repo: ICaseRepository, mock_state_manager, sample_case: Case):
        # Given
        mock_state_manager.state["cases"] = {
            "case001": sample_case.model_dump(),
            "case002": sample_case.model_dump() # dummy data
        }

        # When
        ids = case_repo.get_all_case_ids()

        # Then
        assert sorted(ids) == ["case001", "case002"]

class TestJobRepository:
    @pytest.fixture
    def job_repo(self, mock_state_manager) -> IJobRepository:
        return JobRepository(mock_state_manager)

    @pytest.fixture
    def sample_job(self) -> Job:
        return Job(
            job_id="job001",
            case_id="case001",
            status=JobStatus.PENDING,
            gpu_allocation=[],
            priority=1,
            created_at=datetime.utcnow()
        )

    def test_save_job(self, job_repo: IJobRepository, mock_state_manager, sample_job: Job):
        # When
        job_repo.save(sample_job)

        # Then
        mock_state_manager.transaction.assert_called_once()
        assert mock_state_manager.state["jobs"]["job001"] == sample_job.model_dump()

    def test_find_by_case_id(self, job_repo: IJobRepository, mock_state_manager, sample_job: Job):
        # Given
        another_job = sample_job.copy(update={"job_id": "job002"})
        job_for_other_case = sample_job.copy(update={"job_id": "job003", "case_id": "case002"})

        mock_state_manager.state["jobs"] = {
            "job001": sample_job.model_dump(),
            "job002": another_job.model_dump(),
            "job003": job_for_other_case.model_dump()
        }

        # When
        jobs = job_repo.find_by_case_id("case001")

        # Then
        assert len(jobs) == 2
        assert {job.job_id for job in jobs} == {"job001", "job002"}
