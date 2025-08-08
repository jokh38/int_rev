from typing import Protocol, List, Optional
from mqi_communicator.domain.models import Case, Job

class ICaseService(Protocol):
    """
    Handles business logic related to Cases.
    """
    def scan_for_new_cases(self) -> List[str]:
        """Scans the source directory for new cases and registers them."""
        ...

    def get_case(self, case_id: str) -> Optional[Case]:
        """Retrieves a case by its ID."""
        ...

    def update_case_status(self, case_id: str, status: str) -> None:
        """Updates the status of a case."""
        ...

class IResourceService(Protocol):
    """
    Manages system resources like GPUs and disk space.
    """
    def allocate_gpus(self, count: int) -> List[int]:
        """Allocates a specified number of GPUs."""
        ...

    def release_gpus(self, gpu_ids: List[int]) -> None:
        """Releases a list of GPUs back to the available pool."""
        ...

    def check_disk_space(self) -> bool:
        """Checks if there is sufficient disk space available."""
        ...

class IJobService(Protocol):
    """
    Handles business logic related to Jobs.
    """
    def create_job(self, case_id: str) -> Job:
        """Creates a new job for a given case."""
        ...

    def allocate_resources(self, job: Job) -> bool:
        """Attempts to allocate necessary resources for a job."""
        ...

    def complete_job(self, job_id: str) -> None:
        """Marks a job as complete and releases its resources."""
        ...

class ITransferService(Protocol):
    """
    Orchestrates file transfers between the local machine and a remote host.
    """
    def upload_case(self, case_id: str) -> None:
        """Uploads all files for a given case to the remote host."""
        ...

    def download_results(self, case_id: str) -> None:
        """Downloads the results for a given case from the remote host."""
        ...
