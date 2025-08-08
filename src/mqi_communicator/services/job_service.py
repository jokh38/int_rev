from typing import Optional
from datetime import datetime
import uuid

from mqi_communicator.domain.models import Job, JobStatus
from mqi_communicator.domain.repositories.interfaces import IJobRepository
from .interfaces import IJobService, IResourceService

class JobService(IJobService):
    """
    Handles business logic related to Jobs.
    """
    def __init__(self, job_repository: IJobRepository, resource_service: IResourceService):
        self._repo = job_repository
        self._resource_service = resource_service

    def create_job(self, case_id: str, priority: int = 1) -> Job:
        """
        Creates a new job for a given case.
        """
        new_job = Job(
            job_id=str(uuid.uuid4()),
            case_id=case_id,
            status=JobStatus.PENDING,
            gpu_allocation=[],
            priority=priority,
            created_at=datetime.utcnow()
        )
        self._repo.save(new_job)
        return new_job

    def allocate_resources(self, job: Job, required_gpus: int) -> bool:
        """
        Attempts to allocate necessary resources for a job.
        Returns True if successful, False otherwise.
        """
        allocated_gpus = self._resource_service.allocate_gpus(required_gpus)
        if allocated_gpus:
            job.gpu_allocation = allocated_gpus
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self._repo.save(job)
            return True
        return False

    def complete_job(self, job_id: str) -> None:
        """
        Marks a job as complete and releases its resources.
        """
        job = self._repo.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            # Release resources first
            if job.gpu_allocation:
                self._resource_service.release_gpus(job.gpu_allocation)

            # Update job status
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            self._repo.save(job)
        else:
            # Log warning about completing a non-running or non-existent job
            pass
