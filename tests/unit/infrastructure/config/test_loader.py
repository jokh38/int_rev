import pytest
import yaml
from pathlib import Path

# Target for testing (will be created after the test)
from mqi_communicator.infrastructure.config.loader import ConfigLoader
from mqi_communicator.infrastructure.config.models import MainConfig
from mqi_communicator.exceptions import ConfigurationError, ValidationError

# A fixture to create a temporary config file
@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    content = {
        "paths": {
            "local_logdata": "/test/local",
            "remote_workspace": "/test/remote",
        },
        "ssh": {
            "host": "testhost",
            "username": "testuser",
        },
        "processing": {
            "scan_interval_seconds": 30,
        }
    }
    file_path = tmp_path / "config.yaml"
    with open(file_path, "w") as f:
        yaml.dump(content, f)
    return file_path

@pytest.fixture
def minimal_config_file(tmp_path: Path) -> Path:
    content = {
        "paths": {
            "local_logdata": "/test/local",
            "remote_workspace": "/test/remote",
        },
        "ssh": {
            "host": "testhost",
            "username": "testuser",
        },
    }
    file_path = tmp_path / "config.yaml"
    with open(file_path, "w") as f:
        yaml.dump(content, f)
    return file_path


class TestConfigLoader:
    def test_load_config_success(self, config_file: Path):
        # When
        config = ConfigLoader.load_config(str(config_file))

        # Then
        assert isinstance(config, MainConfig)
        assert config.paths.local_logdata == "/test/local"
        assert config.ssh.host == "testhost"
        assert config.processing.scan_interval_seconds == 30
        # Check a default value
        assert config.app.name == "MQI Communicator"

    def test_load_config_uses_defaults(self, minimal_config_file: Path):
        # When
        config = ConfigLoader.load_config(str(minimal_config_file))

        # Then
        assert config.processing.scan_interval_seconds == 60  # Default value
        assert config.resources.max_concurrent_jobs == 10 # Default value
        assert config.ssh.port == 22 # Default value

    def test_load_config_missing_required_field_raises_error(self, tmp_path: Path):
        # Given
        content = {
            "paths": {
                "local_logdata": "/test/local",
                # remote_workspace is missing
            },
            "ssh": {
                "host": "testhost",
                "username": "testuser",
            },
        }
        file_path = tmp_path / "config.yaml"
        with open(file_path, "w") as f:
            yaml.dump(content, f)

        # When / Then
        with pytest.raises(ValidationError, match="Missing required configuration field: paths.remote_workspace"):
            ConfigLoader.load_config(str(file_path))

    def test_load_config_invalid_type_raises_error(self, tmp_path: Path):
        # Given
        content = {
            "paths": {
                "local_logdata": "/test/local",
                "remote_workspace": "/test/remote",
            },
            "ssh": {
                "host": "testhost",
                "username": "testuser",
                "port": "not-an-integer" # Invalid type
            },
        }
        file_path = tmp_path / "config.yaml"
        with open(file_path, "w") as f:
            yaml.dump(content, f)

        # When / Then
        with pytest.raises(ValidationError, match="Invalid type for field ssh.port"):
            ConfigLoader.load_config(str(file_path))

    def test_load_config_file_not_found_raises_error(self):
        # When / Then
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            ConfigLoader.load_config("non_existent_file.yaml")
