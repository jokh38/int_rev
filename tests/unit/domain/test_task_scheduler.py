import pytest
from unittest.mock import MagicMock
import uuid

# Domain models
from mqi_communicator.domain.models import Task, TaskType, TaskStatus, Case, CaseStatus, Job, JobStatus

# Service interfaces
from mqi_communicator.services.interfaces import ICaseService, IJobService

# Target for testing
from mqi_communicator.domain.task_scheduler import TaskScheduler

@pytest.fixture
def mock_case_service():
    return MagicMock(spec=ICaseService)

@pytest.fixture
def mock_job_service():
    # When a job is created, return a mock Job object
    mock_job = Job(job_id="job-123", case_id="case-abc", status=JobStatus.PENDING, gpu_allocation=[], priority=1, created_at=None)
    service = MagicMock(spec=IJobService)
    service.create_job.return_value = mock_job
    return service

@pytest.fixture
def scheduler(mock_case_service, mock_job_service) -> TaskScheduler:
    return TaskScheduler(case_service=mock_case_service, job_service=mock_job_service)

class TestTaskScheduler:
    def test_schedule_case(self, scheduler: TaskScheduler, mock_job_service):
        # Given
        case_id = "case-to-schedule"

        # When
        tasks = scheduler.schedule_case(case_id)

        # Then
        # Verify a job was created for the case
        mock_job_service.create_job.assert_called_once_with(case_id=case_id)

        # Verify the correct sequence of tasks was generated
        assert len(tasks) == 5
        expected_task_types = [
            TaskType.UPLOAD,
            TaskType.INTERPRET,
            TaskType.BEAM_CALC,
            TaskType.CONVERT,
            TaskType.DOWNLOAD,
        ]
        actual_task_types = [task.type for task in tasks]
        assert actual_task_types == expected_task_types

        # Check that all tasks have the correct job_id and initial status
        for task in tasks:
            assert task.job_id == "job-123"
            assert task.status == TaskStatus.PENDING

    def test_get_next_task(self, scheduler: TaskScheduler):
        # Given
        # Schedule a case to populate the task queue
        tasks = scheduler.schedule_case("case-1")

        # When
        next_task = scheduler.get_next_task()

        # Then
        assert next_task is not None
        assert next_task.type == TaskType.UPLOAD # FIFO queue
        assert next_task == tasks[0]

    def test_get_next_task_from_empty_queue(self, scheduler: TaskScheduler):
        # When
        next_task = scheduler.get_next_task()

        # Then
        assert next_task is None

    def test_complete_task(self, scheduler: TaskScheduler):
        # Given
        tasks = scheduler.schedule_case("case-1")

        # When
        # Get and complete the first task
        task_to_complete = scheduler.get_next_task()
        scheduler.complete_task(task_to_complete.task_id)

        # Then
        # The completed task should no longer be in the queue
        # The next task should be the second one
        next_task = scheduler.get_next_task()
        assert next_task is not None
        assert next_task.type == TaskType.INTERPRET

        # Check that the completed task's status was updated (if we were to check it)
        # This is harder to test without a task repository, but the logic should be there.
        # For now, we just test the queue behavior.

    def test_task_queue_is_fifo(self, scheduler: TaskScheduler):
        # Given
        scheduler.schedule_case("case-1")

        # When
        task1 = scheduler.get_next_task()
        task2 = scheduler.get_next_task()

        # Then
        assert task1.type == TaskType.UPLOAD
        assert task2.type == TaskType.INTERPRET
