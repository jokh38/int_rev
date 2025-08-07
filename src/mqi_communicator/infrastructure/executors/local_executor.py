import subprocess
from typing import Optional

from .interfaces import IExecutor, ExecutionResult
from mqi_communicator.exceptions import ExecutorError

class LocalExecutor(IExecutor):
    """
    Executes commands on the local machine.
    """
    def execute(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Executes a command using subprocess.
        """
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False # Do not raise CalledProcessError automatically
            )
            return ExecutionResult(
                stdout=process.stdout,
                stderr=process.stderr,
                return_code=process.returncode
            )
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"Command '{command}' timed out after {timeout} seconds.") from e
        except Exception as e:
            raise ExecutorError(f"Failed to execute local command: {e}") from e
