from typing import List, Optional
from collections import deque
import uuid

from mqi_communicator.domain.models import Task, TaskType, TaskStatus
from mqi_communicator.services.interfaces import ICaseService, IJobService
from .interfaces import ITaskScheduler

class TaskScheduler(ITaskScheduler):
    """
    Schedules and manages tasks for processing cases.
    This is a simple in-memory implementation. A more robust implementation
    might use a persistent message queue.
    """
    def __init__(self, case_service: ICaseService, job_service: IJobService):
        self._case_service = case_service
        self._job_service = job_service
        self._task_queue: deque[Task] = deque()
        self._active_tasks: dict[str, Task] = {}

    def schedule_case(self, case_id: str) -> List[Task]:
        """
        Generates and schedules a list of tasks required to process a case.
        """
        # Create a job for the case first
        job = self._job_service.create_job(case_id=case_id)

        # Define the standard workflow of tasks
        task_types = [
            TaskType.UPLOAD,
            TaskType.INTERPRET,
            TaskType.BEAM_CALC,
            TaskType.CONVERT,
            TaskType.DOWNLOAD,
        ]

        new_tasks = []
        for task_type in task_types:
            task = Task(
                task_id=str(uuid.uuid4()),
                job_id=job.job_id,
                type=task_type,
                status=TaskStatus.PENDING,
                parameters={} # Parameters could be added here
            )
            new_tasks.append(task)

        self._task_queue.extend(new_tasks)
        return new_tasks

    def get_next_task(self) -> Optional[Task]:
        """
        Retrieves the next task to be executed from the queue.
        """
        if not self._task_queue:
            return None

        task = self._task_queue.popleft()
        task.status = TaskStatus.RUNNING
        self._active_tasks[task.task_id] = task
        return task

    def complete_task(self, task_id: str) -> None:
        """
        Marks a task as complete.
        """
        if task_id in self._active_tasks:
            task = self._active_tasks.pop(task_id)
            task.status = TaskStatus.COMPLETED
            # In a real system, we might save the task's final state here.
        else:
            # Log a warning about an unknown or already completed task
            pass
