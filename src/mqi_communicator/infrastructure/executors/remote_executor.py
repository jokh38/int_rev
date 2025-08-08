from typing import Optional

from .interfaces import IExecutor, ExecutionResult
from mqi_communicator.infrastructure.connection.interfaces import IConnectionPool
from mqi_communicator.exceptions import ExecutorError
import paramiko

class RemoteExecutor(IExecutor):
    """
    Executes commands on a remote machine via an SSH connection pool.
    """
    def __init__(self, connection_pool: IConnectionPool[paramiko.SSHClient]):
        self._connection_pool = connection_pool

    def execute(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Executes a remote command using a connection from the pool.
        """
        try:
            with self._connection_pool.get_connection() as ssh_client:
                stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)

                # Reading the output
                stdout_str = stdout.read().decode('utf-8')
                stderr_str = stderr.read().decode('utf-8')

                # Getting the exit status
                # This is a blocking call, it waits for the command to finish
                return_code = stdout.channel.recv_exit_status()

                return ExecutionResult(
                    stdout=stdout_str,
                    stderr=stderr_str,
                    return_code=return_code
                )
        except Exception as e:
            # Catch paramiko exceptions, timeout errors, etc.
            raise ExecutorError(f"Failed to execute remote command: {e}") from e
