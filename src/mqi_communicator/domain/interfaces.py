from typing import Protocol, List, Optional
from mqi_communicator.domain.models import Task
from dataclasses import dataclass

@dataclass
class GPUStatus:
    id: int
    load: float
    memory_usage: float

@dataclass
class DiskUsage:
    total_gb: float
    used_gb: float
    free_gb: float

class ISystemMonitor(Protocol):
    """
    Interface for a component that monitors system resources.
    """
    def get_cpu_usage(self) -> float: ...
    def get_gpu_status(self) -> List[GPUStatus]: ...
    def get_disk_usage(self, path: str) -> DiskUsage: ...

class ITaskScheduler(Protocol):
    """
    Interface for a component that schedules tasks for cases.
    """
    def schedule_case(self, case_id: str) -> List[Task]:
        """Generates and schedules a list of tasks required to process a case."""
        ...

    def get_next_task(self) -> Optional[Task]:
        """Retrieves the next task to be executed from the queue."""
        ...

    def complete_task(self, task_id: str) -> None:
        """Marks a task as complete."""
        ...

class IWorkflowOrchestrator(Protocol):
    """
    Interface for the main workflow orchestrator.
    """
    def start(self) -> None:
        """Starts the main processing loop."""
        ...

    def stop(self) -> None:
        """Stops the main processing loop gracefully."""
        ...

    def process_case(self, case_id: str) -> None:
        """Processes a single case on demand."""
        ...
