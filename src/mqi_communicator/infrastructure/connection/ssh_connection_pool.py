import queue
import threading
from contextlib import contextmanager
from typing import Dict, Any, ContextManager
import paramiko

from .interfaces import IConnectionPool
from mqi_communicator.infrastructure.config.models import SSHConfig

class SSHConnectionPool(IConnectionPool[paramiko.SSHClient]):
    """
    A thread-safe pool of SSH connections using paramiko.
    """

    def __init__(self, ssh_config: Dict[str, Any], pool_size: int = 5):
        self._ssh_config = ssh_config
        self._pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        for _ in range(self._pool_size):
            self._pool.put(self._create_connection())

    def _create_connection(self) -> paramiko.SSHClient:
        """Creates a new SSH connection."""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=self._ssh_config['host'],
                port=self._ssh_config.get('port', 22),
                username=self._ssh_config['username'],
                key_filename=self._ssh_config.get('key_file'),
                # Add other paramiko options as needed, e.g., password
            )
            return client
        except Exception as e:
            # Handle connection errors, maybe log them
            raise ConnectionError(f"Failed to create SSH connection: {e}") from e

    @contextmanager
    def get_connection(self, timeout: float = 30.0) -> ContextManager[paramiko.SSHClient]:
        """
        Provides a connection from the pool. Blocks if the pool is empty.
        """
        connection = self._pool.get(block=True, timeout=timeout)
        try:
            # Before yielding the connection, check if it's still alive.
            if not connection.get_transport() or not connection.get_transport().is_active():
                # Connection is dead, create a new one to replace it.
                try:
                    connection.close()
                except Exception:
                    pass # Ignore errors on closing a dead connection
                connection = self._create_connection()

            yield connection
        finally:
            # Always return the connection to the pool.
            self._pool.put(connection)

    def shutdown(self):
        """
        Closes all connections in the pool.
        """
        with self._lock:
            while not self._pool.empty():
                conn = self._pool.get()
                try:
                    conn.close()
                except Exception:
                    # Ignore errors during shutdown
                    pass
