import pytest
import docker
import time
from pathlib import Path
import tempfile
import shutil

from mqi_communicator.container import Container

@pytest.fixture(scope="session")
def ssh_server():
    """
    A session-scoped fixture that starts and stops an SSH server using Docker.
    """
    compose_file = Path(__file__).parent.parent.parent / "docker-compose.test.yml"
    if not compose_file.exists():
        pytest.skip("docker-compose.test.yml not found, skipping integration tests.")

    client = docker.from_env()

    try:
        print("\nStarting SSHD container...")
        # Using docker-compose equivalent in python is complex, let's assume
        # a user would run `docker-compose up` before the tests.
        # For programmatic control, we run the container directly.
        container = client.containers.run(
            "linuxserver/openssh-server",
            name="mqi_test_sshd_fixture",
            ports={'2222/tcp': 2222},
            environment={
                "USER_NAME": "testuser",
                "USER_PASSWORD": "testpassword", # A more secure way should be used
                "PASSWORD_ACCESS": "true",
            },
            detach=True,
            remove=True, # Automatically remove container on exit
        )
        # Wait for the container to be ready
        time.sleep(5)
        yield container
        print("\nStopping SSHD container...")
    finally:
        try:
            container.stop()
        except NameError:
            # Container failed to start
            pass


@pytest.fixture
def test_workspace():
    """
    Creates a temporary local workspace for a test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "local_data").mkdir()
        (workspace / "state").mkdir()
        (workspace / "pids").mkdir()
        yield workspace


@pytest.fixture
def test_container(ssh_server, test_workspace: Path) -> Container:
    """
    Provides a fully configured DI container for integration tests.
    """
    container = Container()
    config = {
        "paths": {
            "local_logdata": str(test_workspace / "local_data"),
            "remote_workspace": "/home/testuser/workspace",
            "state_file": str(test_workspace / "state" / "state.json"),
            "pid_file": str(test_workspace / "pids" / "mqi.pid"),
        },
        "ssh": {
            "host": "localhost",
            "port": 2222,
            "username": "testuser",
            "password": "testpassword", # For paramiko to connect
        },
        "processing": {"scan_interval_seconds": 1},
        "resources": {"total_gpu_count": 1, "min_disk_space_gb": 1},
    }
    container.config.from_dict(config)
    container.wire(modules=["mqi_communicator.main"])
    yield container
    container.unwire()
