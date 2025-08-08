import pytest
from dependency_injector import containers, providers

# The container to be tested
from mqi_communicator.container import Container

# Import some key components to check their types
from mqi_communicator.domain.workflow_orchestrator import WorkflowOrchestrator
from mqi_communicator.services.case_service import CaseService
from mqi_communicator.infrastructure.state.json_state_manager import JsonStateManager

@pytest.fixture
def config_dict():
    """A sample configuration dictionary for testing the container."""
    return {
        "paths": {
            "local_logdata": "/tmp/local",
            "remote_workspace": "/tmp/remote",
            "state_file": "/tmp/state.json",
            "pid_file": "/tmp/mqi.pid"
        },
        "ssh": {
            "host": "localhost",
            "username": "test",
            "port": 2222
        },
        "processing": {
            "scan_interval_seconds": 10
        },
        "resources": {
            "total_gpu_count": 2,
            "min_disk_space_gb": 5
        }
    }

@pytest.fixture
def container(config_dict):
    """Fixture to create and wire a container instance."""
    c = Container()
    c.config.from_dict(config_dict)
    # Wire the container to instantiate the providers
    c.wire(
        modules=[
            # We would wire modules here if they used dependency injection
        ]
    )
    yield c
    # Unwire after the test
    c.unwire()

class TestContainer:
    def test_container_creation(self, container: Container):
        assert container is not None
        assert container.config.paths.local_logdata() == "/tmp/local"

    def test_state_manager_is_singleton(self, container: Container):
        sm1 = container.infrastructure.state_manager()
        sm2 = container.infrastructure.state_manager()
        assert sm1 is sm2
        assert isinstance(sm1, JsonStateManager)

    def test_case_service_creation(self, container: Container):
        case_service = container.services.case_service()
        assert isinstance(case_service, CaseService)
        # Check that its dependencies were injected
        assert case_service._repo is container.repositories.case_repository()

    def test_workflow_orchestrator_creation(self, container: Container):
        orchestrator = container.domain.workflow_orchestrator()
        assert isinstance(orchestrator, WorkflowOrchestrator)
        # Check that its dependencies were injected
        assert orchestrator._case_service is container.services.case_service()
        assert orchestrator._task_scheduler is container.domain.task_scheduler()

    def test_override_provider_for_testing(self, container: Container, config_dict):
        # This demonstrates how we can override providers for integration tests
        mock_orchestrator = providers.Singleton(MagicMock)

        with container.domain.workflow_orchestrator.override(mock_orchestrator):
            instance = container.domain.workflow_orchestrator()
            assert isinstance(instance, MagicMock)

        # Check that the override is gone
        instance_after = container.domain.workflow_orchestrator()
        assert isinstance(instance_after, WorkflowOrchestrator)
