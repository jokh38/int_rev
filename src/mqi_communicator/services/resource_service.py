from typing import List
import shutil

from mqi_communicator.domain.repositories.interfaces import IResourceRepository
from .interfaces import IResourceService

class ResourceService(IResourceService):
    """
    Manages system resources like GPUs and disk space.
    """
    def __init__(self, resource_repository: IResourceRepository, total_gpu_count: int, min_disk_space_gb: int):
        self._repo = resource_repository
        self._total_gpu_count = total_gpu_count
        self._min_disk_space_gb = min_disk_space_gb
        self._all_gpus = set(range(total_gpu_count))

    def allocate_gpus(self, count: int) -> List[int]:
        """
        Allocates a specified number of GPUs.
        Returns a list of GPU IDs if successful, otherwise an empty list.
        """
        allocated_gpus = set(self._repo.get_allocated_gpus())
        available_gpus = sorted(list(self._all_gpus - allocated_gpus))

        if len(available_gpus) >= count:
            gpus_to_allocate = available_gpus[:count]
            newly_allocated_gpus = sorted(list(allocated_gpus.union(gpus_to_allocate)))
            self._repo.set_allocated_gpus(newly_allocated_gpus)
            return gpus_to_allocate
        else:
            return []

    def release_gpus(self, gpu_ids: List[int]) -> None:
        """
        Releases a list of GPUs back to the available pool.
        """
        allocated_gpus = set(self._repo.get_allocated_gpus())
        gpus_to_release = set(gpu_ids)

        newly_allocated_gpus = sorted(list(allocated_gpus - gpus_to_release))
        self._repo.set_allocated_gpus(newly_allocated_gpus)

    def check_disk_space(self, path: str) -> bool:
        """
        Checks if there is sufficient disk space available in the given path.
        """
        free_space_bytes = shutil.disk_usage(path).free
        free_space_gb = free_space_bytes / (1024**3)
        return free_space_gb >= self._min_disk_space_gb
