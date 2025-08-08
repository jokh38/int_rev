from mqi_communicator.infrastructure.executors.interfaces import IExecutor
from mqi_communicator.infrastructure.config.models import PathsConfig, SSHConfig
from mqi_communicator.exceptions import TransferError
from .interfaces import ITransferService

class TransferService(ITransferService):
    """
    Orchestrates file transfers between the local machine and a remote host.
    """
    def __init__(self, remote_executor: IExecutor, paths_config: PathsConfig, ssh_config: SSHConfig):
        self._executor = remote_executor
        self._paths = paths_config
        self._ssh = ssh_config

    def _build_rsync_command(self, source: str, destination: str) -> str:
        """Helper to build a standard rsync command."""
        # This could be made more robust, e.g., handling key files, passwords etc.
        # For now, it assumes key-based auth is set up.
        remote_target = f"{self._ssh.username}@{self._ssh.host}"

        # Replace remote host placeholder in paths
        source = source.replace("user@host:", f"{remote_target}:")
        destination = destination.replace("user@host:", f"{remote_target}:")

        # Use -e to specify ssh port if not default 22
        ssh_command = "ssh"
        if self._ssh.port != 22:
            ssh_command = f"ssh -p {self._ssh.port}"

        return f"rsync -az --progress -e '{ssh_command}' {source} {destination}"

    def upload_case(self, case_id: str) -> None:
        """
        Uploads all files for a given case to the remote host.
        """
        local_path = f"{self._paths.local_logdata}/{case_id}/"
        remote_path = f"user@host:{self._paths.remote_workspace}/"

        command = self._build_rsync_command(local_path, remote_path)

        result = self._executor.execute(command)

        if not result.succeeded():
            raise TransferError(f"Failed to upload case {case_id}: {result.stderr}")

    def download_results(self, case_id: str) -> None:
        """
        Downloads the results for a given case from the remote host.
        """
        # Assuming results are in a sub-directory named 'results'
        remote_path = f"user@host:{self._paths.remote_workspace}/{case_id}/results/"
        local_path = f"{self._paths.local_logdata}/{case_id}/"

        command = self._build_rsync_command(remote_path, local_path)

        result = self._executor.execute(command)

        if not result.succeeded():
            raise TransferError(f"Failed to download results for case {case_id}: {result.stderr}")
