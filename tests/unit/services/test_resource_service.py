import pytest
from unittest.mock import MagicMock, patch

# Target for testing
from mqi_communicator.services.resource_service import ResourceService

# A mock for the resource repository that would live in the infrastructure layer
@pytest.fixture
def mock_resource_repo():
    repo = MagicMock()
    # Simulate 4 available GPUs
    repo.get_available_gpus.return_value = [0, 1, 2, 3]
    return repo

@pytest.fixture
def resource_service(mock_resource_repo) -> ResourceService:
    # Assume the service takes the total number of GPUs from a config
    # and uses a repository to track state.
    return ResourceService(resource_repository=mock_resource_repo, total_gpu_count=4)

class TestResourceService:
    def test_allocate_gpus_success(self, resource_service: ResourceService, mock_resource_repo):
        # When
        allocated_gpus = resource_service.allocate_gpus(2)

        # Then
        assert allocated_gpus == [0, 1]
        mock_resource_repo.set_allocated_gpus.assert_called_once_with([0, 1])

    def test_allocate_gpus_insufficient_resources(self, resource_service: ResourceService, mock_resource_repo):
        # Given
        # Only 1 GPU is available
        mock_resource_repo.get_available_gpus.return_value = [3]

        # When
        allocated_gpus = resource_service.allocate_gpus(2)

        # Then
        assert allocated_gpus == []
        mock_resource_repo.set_allocated_gpus.assert_not_called()

    def test_release_gpus(self, resource_service: ResourceService, mock_resource_repo):
        # Given
        # Pretend GPUs 0 and 1 were allocated
        mock_resource_repo.get_allocated_gpus.return_value = [0, 1]

        # When
        resource_service.release_gpus([0, 1])

        # Then
        # The repository should be updated to have no allocated GPUs
        mock_resource_repo.set_allocated_gpus.assert_called_once_with([])

    @patch('shutil.disk_usage')
    def test_check_disk_space_sufficient(self, mock_disk_usage):
        # Given
        # Mock shutil.disk_usage to return plenty of free space (e.g., 200 GB)
        mock_disk_usage.return_value.free = 200 * (1024**3)
        # Service is configured to require 100 GB
        service = ResourceService(MagicMock(), total_gpu_count=4, min_disk_space_gb=100)

        # When
        result = service.check_disk_space("/fake/path")

        # Then
        assert result is True

    @patch('shutil.disk_usage')
    def test_check_disk_space_insufficient(self, mock_disk_usage):
        # Given
        # Mock shutil.disk_usage to return only 50 GB of free space
        mock_disk_usage.return_value.free = 50 * (1024**3)
        service = ResourceService(MagicMock(), total_gpu_count=4, min_disk_space_gb=100)

        # When
        result = service.check_disk_space("/fake/path")

        # Then
        assert result is False
