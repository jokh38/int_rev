from typing import Protocol, List, Optional
from mqi_communicator.domain.models import Case, Job

class ICaseRepository(Protocol):
    """
    Interface for a repository that manages Case objects.
    """
    def save(self, case: Case) -> None:
        """Saves a case object (creates or updates)."""
        ...

    def get(self, case_id: str) -> Optional[Case]:
        """Retrieves a case by its ID."""
        ...

    def get_all(self) -> List[Case]:
        """Retrieves all cases."""
        ...

    def get_all_case_ids(self) -> List[str]:
        """Retrieves all case IDs."""
        ...


class IJobRepository(Protocol):
    """
    Interface for a repository that manages Job objects.
    """
    def save(self, job: Job) -> None:
        """Saves a job object (creates or updates)."""
        ...

    def get(self, job_id: str) -> Optional[Job]:
        """Retrieves a job by its ID."""
        ...

    def get_all(self) -> List[Job]:
        """Retrieves all jobs."""
        ...

    def find_by_case_id(self, case_id: str) -> List[Job]:
        """Finds all jobs associated with a given case ID."""
        ...


class IResourceRepository(Protocol):
    """
    Interface for a repository that manages system resource state.
    """
    def get_allocated_gpus(self) -> List[int]:
        """Returns a list of currently allocated GPU IDs."""
        ...

    def set_allocated_gpus(self, gpu_ids: List[int]) -> None:
        """Sets the list of allocated GPU IDs."""
        ...
