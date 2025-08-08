from .interfaces import ILifecycleManager
from mqi_communicator.domain.interfaces import IWorkflowOrchestrator
from mqi_communicator.infrastructure.config.models import MonitoringConfig
from prometheus_client import start_http_server
import logging

logger = logging.getLogger(__name__)

class Application:
    """
    The main application class.
    It orchestrates the lifecycle and the main workflow.
    """
    def __init__(
        self,
        lifecycle_manager: ILifecycleManager,
        workflow_orchestrator: IWorkflowOrchestrator,
        monitoring_config: MonitoringConfig,
    ):
        self._lifecycle_manager = lifecycle_manager
        self._orchestrator = workflow_orchestrator
        self._monitoring_config = monitoring_config

    def run(self):
        """
        Starts and runs the application.
        """
        # Start metrics server
        try:
            start_http_server(self._monitoring_config.metrics_port)
            logger.info(f"Prometheus metrics server started on port {self._monitoring_config.metrics_port}")
        except Exception as e:
            logger.error(f"Could not start Prometheus metrics server: {e}")
            # Decide if this is a fatal error. For now, we'll just log it.

        if not self._lifecycle_manager.acquire_lock():
            print("Application lock could not be acquired. Exiting.")
            return

        # Register the orchestrator's stop method as the primary shutdown task
        self._lifecycle_manager.register_shutdown_handler(self.shutdown)

        print("Application started. Press Ctrl+C to exit.")
        self._orchestrator.start()

        # The main thread can now just wait for a shutdown signal.
        # The LifecycleManager's signal handler will exit the process.
        # Or, if the orchestrator thread is not a daemon, we could join it.
        # Since it's a daemon, we'll just let the main thread finish,
        # and the daemon will be terminated when the app exits.
        # A better approach is to have the orchestrator loop block until
        # its stop event is set, and join() it here.
        # For now, this is sufficient. The signal handler will manage exit.

        # This is a placeholder for keeping the main thread alive.
        # In a real app, we might join a non-daemon thread or wait on an event.
        try:
            while True:
                # Keep the main thread alive to receive signals
                # The orchestrator is running in a daemon thread.
                time.sleep(1)
        except KeyboardInterrupt:
            # This is handled by the signal handler, but as a fallback:
            self.shutdown()


    def shutdown(self):
        """
        Performs a graceful shutdown of the application.
        """
        print("Shutting down application...")
        self._orchestrator.stop()
        self._lifecycle_manager.release_lock()
        print("Application shutdown complete.")

# This import is needed for the placeholder in run()
import time
