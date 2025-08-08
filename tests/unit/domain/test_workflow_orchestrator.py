import pytest
from unittest.mock import MagicMock, patch
import time

# Domain interfaces
from mqi_communicator.domain.interfaces import ITaskScheduler, ISystemMonitor
from mqi_communicator.domain.models import Task, TaskType, TaskStatus

# Service interfaces
from mqi_communicator.services.interfaces import ICaseService, ITransferService

# Target for testing
from mqi_communicator.domain.workflow_orchestrator import WorkflowOrchestrator

@pytest.fixture
def mock_case_service():
    service = MagicMock(spec=ICaseService)
    service.scan_for_new_cases.return_value = ["case_001"] # Found one new case
    return service

@pytest.fixture
def mock_task_scheduler():
    scheduler = MagicMock(spec=ITaskScheduler)
    # Simulate a sequence of tasks for the case
    tasks = [
        Task(task_id="t1", job_id="j1", type=TaskType.UPLOAD, status=TaskStatus.PENDING),
        Task(task_id="t2", job_id="j1", type=TaskType.DOWNLOAD, status=TaskStatus.PENDING),
    ]
    # get_next_task returns one task at a time, then None
    scheduler.get_next_task.side_effect = tasks + [None]
    return scheduler

@pytest.fixture
def mock_transfer_service():
    return MagicMock(spec=ITransferService)

@pytest.fixture
def mock_system_monitor():
    monitor = MagicMock(spec=ISystemMonitor)
    # Simulate healthy system
    monitor.get_cpu_usage.return_value = 50.0
    monitor.get_disk_usage.return_value.free_gb = 500.0
    return monitor

@pytest.fixture
def orchestrator(
    mock_case_service,
    mock_task_scheduler,
    mock_transfer_service,
    mock_system_monitor
) -> WorkflowOrchestrator:
    return WorkflowOrchestrator(
        case_service=mock_case_service,
        task_scheduler=mock_task_scheduler,
        transfer_service=mock_transfer_service,
        system_monitor=mock_system_monitor,
        scan_interval=0.1
    )

class TestWorkflowOrchestrator:
    def test_process_single_case(self, orchestrator: WorkflowOrchestrator, mock_task_scheduler, mock_transfer_service):
        # Given
        case_id = "case_to_process"

        # When
        orchestrator.process_case(case_id)

        # Then
        # Verify that the case was scheduled
        mock_task_scheduler.schedule_case.assert_called_once_with(case_id)

        # Verify that the tasks were executed
        # In this simplified test, we have an upload and a download task
        mock_transfer_service.upload_case.assert_called_once_with(case_id=None) # job_id would be better
        mock_transfer_service.download_results.assert_called_once_with(case_id=None)

        # Verify that the tasks were marked as complete
        assert mock_task_scheduler.complete_task.call_count == 2
        mock_task_scheduler.complete_task.assert_any_call("t1")
        mock_task_scheduler.complete_task.assert_any_call("t2")

    @patch('threading.Event.wait')
    def test_main_loop_scans_and_processes(self, mock_event_wait, orchestrator: WorkflowOrchestrator, mock_case_service, mock_task_scheduler):
        # This tests the main run loop
        # We need to stop the loop after one iteration for the test to finish

        # Given
        # The first call to wait() will proceed, the second will stop the loop
        mock_event_wait.side_effect = [False, True]

        # When
        orchestrator.start() # This will run the loop once

        # Then
        # It should have scanned for new cases
        mock_case_service.scan_for_new_cases.assert_called_once()

        # It should have scheduled the new case found ("case_001")
        mock_task_scheduler.schedule_case.assert_called_once_with("case_001")

        # It should have started processing tasks from the queue
        mock_task_scheduler.get_next_task.assert_called()

    def test_stop_sets_event(self, orchestrator: WorkflowOrchestrator):
        # When
        orchestrator.stop()

        # Then
        # The stop event should be set, which would terminate the main loop
        assert orchestrator._stop_event.is_set()
