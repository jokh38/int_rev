from dependency_injector import containers, providers

from mqi_communicator.infrastructure.config.loader import ConfigLoader
from mqi_communicator.infrastructure.state.json_state_manager import JsonStateManager
from mqi_communicator.infrastructure.connection.ssh_connection_pool import SSHConnectionPool
from mqi_communicator.infrastructure.executors.local_executor import LocalExecutor
from mqi_communicator.infrastructure.executors.remote_executor import RemoteExecutor
from mqi_communicator.domain.repositories.json_repositories import CaseRepository, JobRepository, IResourceRepository # IResourceRepository needs an impl
from mqi_communicator.services.case_service import CaseService, FileSystem
from mqi_communicator.services.resource_service import ResourceService
from mqi_communicator.services.job_service import JobService
from mqi_communicator.services.transfer_service import TransferService
from mqi_communicator.domain.system_monitor import SystemMonitor
from mqi_communicator.domain.task_scheduler import TaskScheduler
from mqi_communicator.domain.workflow_orchestrator import WorkflowOrchestrator
from mqi_communicator.controllers.lifecycle_manager import LifecycleManager
from mqi_communicator.controllers.application import Application

# A concrete implementation for the resource repository is needed.
# For now, it can be a simple one that uses the same state manager.
class ResourceRepository(IResourceRepository):
    def __init__(self, state_manager: JsonStateManager):
        self._sm = state_manager
        with self._sm.transaction() as tx:
            state = tx.get_state()
            if "resources" not in state:
                state["resources"] = {"allocated_gpus": []}

    def get_allocated_gpus(self) -> list[int]:
        return self._sm.get("resources", {}).get("allocated_gpus", [])

    def set_allocated_gpus(self, gpu_ids: list[int]) -> None:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            state["resources"]["allocated_gpus"] = gpu_ids

class Container(containers.DeclarativeContainer):
    """
    The main dependency injection container for the application.
    """
    config = providers.Configuration()

    # Infrastructure Layer
    state_manager = providers.Singleton(JsonStateManager, state_file=config.paths.state_file)

    ssh_pool = providers.Singleton(
        SSHConnectionPool,
        ssh_config=config.ssh,
        pool_size=config.ssh.connection_pool_size.as_int()
    )

    local_executor = providers.Singleton(LocalExecutor)
    remote_executor = providers.Singleton(RemoteExecutor, connection_pool=ssh_pool)
    file_system = providers.Singleton(FileSystem)

    # Repository Layer
    case_repository = providers.Singleton(CaseRepository, state_manager=state_manager)
    job_repository = providers.Singleton(JobRepository, state_manager=state_manager)
    resource_repository = providers.Singleton(ResourceRepository, state_manager=state_manager)

    # Service Layer
    resource_service = providers.Singleton(
        ResourceService,
        resource_repository=resource_repository,
        total_gpu_count=config.resources.total_gpu_count.as_int(),
        min_disk_space_gb=config.resources.min_disk_space_gb.as_int()
    )
    case_service = providers.Singleton(
        CaseService,
        case_repository=case_repository,
        file_system=file_system,
        scan_path=config.paths.local_logdata
    )
    job_service = providers.Singleton(
        JobService,
        job_repository=job_repository,
        resource_service=resource_service
    )
    transfer_service = providers.Singleton(
        TransferService,
        remote_executor=remote_executor,
        paths_config=config.paths,
        ssh_config=config.ssh
    )

    # Domain Layer
    system_monitor = providers.Singleton(SystemMonitor)
    task_scheduler = providers.Singleton(
        TaskScheduler,
        case_service=case_service,
        job_service=job_service
    )
    workflow_orchestrator = providers.Singleton(
        WorkflowOrchestrator,
        case_service=case_service,
        job_service=job_service,
        task_scheduler=task_scheduler,
        transfer_service=transfer_service,
        system_monitor=system_monitor,
        scan_interval=config.processing.scan_interval_seconds.as_int()
    )

    # Application Layer
    lifecycle_manager = providers.Singleton(LifecycleManager, pid_file=config.paths.pid_file)
    application = providers.Singleton(
        Application,
        lifecycle_manager=lifecycle_manager,
        workflow_orchestrator=workflow_orchestrator
    )
