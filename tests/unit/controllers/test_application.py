import pytest
from unittest.mock import MagicMock

# Interfaces
from mqi_communicator.domain.interfaces import IWorkflowOrchestrator
from mqi_communicator.controllers.interfaces import ILifecycleManager # This interface needs to be created

# Target for testing
from mqi_communicator.controllers.application import Application

# Create the missing interface first
# This is a placeholder, will be created in a separate step
class ILifecycleManager(MagicMock):
    pass

@pytest.fixture
def mock_lifecycle_manager():
    # When acquire_lock is called, it succeeds
    manager = MagicMock(spec=ILifecycleManager)
    manager.acquire_lock.return_value = True
    return manager

@pytest.fixture
def mock_orchestrator():
    return MagicMock(spec=IWorkflowOrchestrator)

@pytest.fixture
def app(mock_lifecycle_manager, mock_orchestrator) -> Application:
    return Application(
        lifecycle_manager=mock_lifecycle_manager,
        workflow_orchestrator=mock_orchestrator
    )

class TestApplication:
    def test_run_success_flow(self, app: Application, mock_lifecycle_manager, mock_orchestrator):
        # When
        app.run()

        # Then
        # 1. Lock is acquired
        mock_lifecycle_manager.acquire_lock.assert_called_once()

        # 2. Shutdown handler is registered
        mock_lifecycle_manager.register_shutdown_handler.assert_called_once()
        # The argument should be the orchestrator's stop method
        shutdown_handler_arg = mock_lifecycle_manager.register_shutdown_handler.call_args[0][0]
        assert shutdown_handler_arg == mock_orchestrator.stop

        # 3. Orchestrator is started
        mock_orchestrator.start.assert_called_once()

        # 4. Lock is released on shutdown (which is part of the handler)
        # This is harder to test without running the full handler logic
        # But we can assume the lifecyclemanager test covers the release_lock call.

    def test_run_aborts_if_lock_not_acquired(self, app: Application, mock_lifecycle_manager, mock_orchestrator):
        # Given
        # The lock acquisition will fail
        mock_lifecycle_manager.acquire_lock.return_value = False

        # When
        app.run()

        # Then
        # Nothing else should be called
        mock_lifecycle_manager.register_shutdown_handler.assert_not_called()
        mock_orchestrator.start.assert_not_called()

    def test_shutdown_is_called(self, app: Application, mock_lifecycle_manager, mock_orchestrator):
        # When
        app.shutdown()

        # Then
        mock_orchestrator.stop.assert_called_once()
        mock_lifecycle_manager.release_lock.assert_called_once()
