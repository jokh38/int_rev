from typing import Protocol, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """
    Represents the result of a command execution.
    """
    stdout: str
    stderr: str
    return_code: int

    def succeeded(self) -> bool:
        return self.return_code == 0

class IExecutor(Protocol):
    """
    An interface for a command executor.
    """
    def execute(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Executes a command.

        Args:
            command: The command string to execute.
            timeout: An optional timeout in seconds.

        Returns:
            An ExecutionResult object containing the output and return code.

        Raises:
            TimeoutError: If the command exceeds the timeout.
            ExecutorError: For other execution-related failures.
        """
        ...
