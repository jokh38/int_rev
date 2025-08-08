import threading
import time
from typing import Dict, Callable

from mqi_communicator.domain.interfaces import (
    IWorkflowOrchestrator, ITaskScheduler, ISystemMonitor
)
from mqi_communicator.services.interfaces import (
    ICaseService, ITransferService, IJobService, IResourceService
)
from mqi_communicator.domain.models import Task, TaskType

class WorkflowOrchestrator(IWorkflowOrchestrator):
    """
    The main workflow orchestrator for the MQI Communicator.
    It runs a continuous loop to process cases.
    """
    def __init__(
        self,
        case_service: ICaseService,
        job_service: IJobService, # Added job_service
        task_scheduler: ITaskScheduler,
        transfer_service: ITransferService,
        system_monitor: ISystemMonitor,
        scan_interval: int = 60,
    ):
        self._case_service = case_service
        self._job_service = job_service
        self._task_scheduler = task_scheduler
        self._transfer_service = transfer_service
        self._system_monitor = system_monitor
        self._scan_interval = scan_interval

        self._main_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Map task types to handler methods
        self._task_handlers: Dict[TaskType, Callable[[Task], None]] = {
            TaskType.UPLOAD: self._handle_upload,
            TaskType.DOWNLOAD: self._handle_download,
            # Other handlers would be defined here
        }

    def start(self) -> None:
        """Starts the main processing loop in a separate thread."""
        if self._main_thread is None or not self._main_thread.is_alive():
            self._stop_event.clear()
            self._main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self._main_thread.start()

    def stop(self) -> None:
        """Stops the main processing loop gracefully."""
        self._stop_event.set()
        if self._main_thread:
            self._main_thread.join()

    def _main_loop(self):
        """The main loop that continuously scans for and processes cases."""
        while not self._stop_event.is_set():
            # 1. Scan for new cases and schedule them
            new_case_ids = self._case_service.scan_for_new_cases()
            for case_id in new_case_ids:
                self._task_scheduler.schedule_case(case_id)

            # 2. Process tasks from the queue
            task = self._task_scheduler.get_next_task()
            if task:
                self.execute_task(task)
            else:
                # If no tasks, wait before the next scan
                self._stop_event.wait(self._scan_interval)

    def process_case(self, case_id: str) -> None:
        """Processes a single case on demand."""
        tasks = self._task_scheduler.schedule_case(case_id)
        for task in tasks:
            self.execute_task(task)

    def execute_task(self, task: Task) -> None:
        """Executes a single task."""
        handler = self._task_handlers.get(task.type)
        if handler:
            try:
                # Get the job associated with the task to pass to the handler
                job = self._job_service.get(task.job_id)
                if job:
                    handler(task, job)
                    self._task_scheduler.complete_task(task.task_id)
                else:
                    # Handle missing job
                    pass
            except Exception:
                # Handle task execution failure
                # e.g., mark task as failed, release resources
                pass
        else:
            # Handle unknown task type
            pass

    # --- Task Handlers ---

    def _handle_upload(self, task: Task, job) -> None:
        self._transfer_service.upload_case(job.case_id)

    def _handle_download(self, task: Task, job) -> None:
        self._transfer_service.download_results(job.case_id)
