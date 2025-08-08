import pytest
from unittest.mock import MagicMock
from datetime import datetime
import uuid

# Domain models and repository interfaces
from mqi_communicator.domain.models import Job, JobStatus, Case
from mqi_communicator.domain.repositories.interfaces import IJobRepository

# Service interfaces
from mqi_communicator.services.interfaces import IResourceService

# Target for testing
from mqi_communicator.services.job_service import JobService

@pytest.fixture
def mock_job_repo():
    return MagicMock(spec=IJobRepository)

@pytest.fixture
def mock_resource_service():
    service = MagicMock(spec=IResourceService)
    # Simulate that GPU allocation is successful
    service.allocate_gpus.return_value = [0]
    return service

@pytest.fixture
def job_service(mock_job_repo, mock_resource_service) -> JobService:
    return JobService(job_repository=mock_job_repo, resource_service=mock_resource_service)

class TestJobService:
    def test_create_job(self, job_service: JobService, mock_job_repo):
        # Given
        case_id = "case_to_process"

        # When
        # Mock uuid.uuid4() to return a predictable job_id
        with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            new_job = job_service.create_job(case_id, priority=5)

        # Then
        assert new_job.case_id == case_id
        assert new_job.priority == 5
        assert new_job.status == JobStatus.PENDING
        assert new_job.job_id == '12345678-1234-5678-1234-567812345678'

        # Verify that the new job was saved
        mock_job_repo.save.assert_called_once_with(new_job)

    def test_allocate_resources_success(self, job_service: JobService, mock_resource_service):
        # Given
        job = Job(
            job_id="job001",
            case_id="case001",
            status=JobStatus.PENDING,
            gpu_allocation=[],
            priority=1,
            created_at=datetime.utcnow()
        )
        # Resource service will successfully allocate 1 GPU
        mock_resource_service.allocate_gpus.return_value = [0]

        # When
        success = job_service.allocate_resources(job, required_gpus=1)

        # Then
        assert success is True
        mock_resource_service.allocate_gpus.assert_called_once_with(1)
        assert job.gpu_allocation == [0]
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_allocate_resources_failure(self, job_service: JobService, mock_resource_service):
        # Given
        job = Job(
            job_id="job001",
            case_id="case001",
            status=JobStatus.PENDING,
            gpu_allocation=[],
            priority=1,
            created_at=datetime.utcnow()
        )
        # Resource service will fail to allocate GPUs
        mock_resource_service.allocate_gpus.return_value = []

        # When
        success = job_service.allocate_resources(job, required_gpus=1)

        # Then
        assert success is False
        assert job.gpu_allocation == []
        assert job.status == JobStatus.PENDING # Status should not change

    def test_complete_job(self, job_service: JobService, mock_resource_service, mock_job_repo):
        # Given
        job = Job(
            job_id="job001",
            case_id="case001",
            status=JobStatus.RUNNING,
            gpu_allocation=[0, 1],
            priority=1,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow()
        )
        mock_job_repo.get.return_value = job

        # When
        job_service.complete_job("job001")

        # Then
        mock_job_repo.get.assert_called_once_with("job001")
        # Check that resources were released
        mock_resource_service.release_gpus.assert_called_once_with([0, 1])
        # Check that job status is updated and saved
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        mock_job_repo.save.assert_called_once_with(job)
