import os
import signal
import psutil
from typing import Callable, List

class LifecycleManager:
    """
    Manages the application's lifecycle, including PID file locking
    and graceful shutdown signal handling.
    """
    def __init__(self, pid_file: str):
        self._pid_file = pid_file
        self._pid = os.getpid()
        self._locked = False
        self._shutdown_handlers: List[Callable] = []

    def acquire_lock(self) -> bool:
        """
        Acquires a PID lock. Returns True if successful, False otherwise.
        """
        if os.path.exists(self._pid_file):
            try:
                with open(self._pid_file, 'r') as f:
                    old_pid = int(f.read().strip())

                if psutil.pid_exists(old_pid):
                    # Process is still running
                    print(f"Another instance with PID {old_pid} is already running.")
                    return False
                else:
                    # Stale PID file
                    print(f"Removing stale PID file for non-existent process {old_pid}.")
                    os.remove(self._pid_file)
            except (IOError, ValueError):
                # PID file is corrupted or unreadable
                print("Removing corrupted PID file.")
                os.remove(self._pid_file)

        # Create new PID file
        try:
            with open(self._pid_file, 'w') as f:
                f.write(str(self._pid))
            self._locked = True
            return True
        except IOError:
            print(f"Unable to create PID file at {self._pid_file}.")
            return False

    def release_lock(self) -> None:
        """
        Releases the PID lock by deleting the PID file.
        """
        if self._locked and os.path.exists(self._pid_file):
            try:
                # Verify we are deleting our own PID file
                with open(self._pid_file, 'r') as f:
                    pid_in_file = int(f.read().strip())
                if pid_in_file == self._pid:
                    os.remove(self._pid_file)
            except (IOError, ValueError):
                pass # Ignore errors on release
        self._locked = False

    def register_shutdown_handler(self, handler: Callable[[], None]):
        """
        Registers a function to be called on graceful shutdown.
        Also sets up the signal handlers if not already done.
        """
        if not self._shutdown_handlers:
            # First handler is being registered, set up the signals
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

        self._shutdown_handlers.append(handler)

    def _signal_handler(self, signum, frame):
        """
        Internal handler that calls all registered shutdown handlers.
        """
        print(f"\nReceived shutdown signal {signum}. Cleaning up...")
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                print(f"Error in shutdown handler: {e}")

        self.release_lock()
        print("Cleanup complete. Exiting.")
        os._exit(0)
