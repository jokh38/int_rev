import yaml
from pathlib import Path
from dataclasses import is_dataclass, fields, MISSING
from typing import Type, TypeVar

from mqi_communicator.infrastructure.config.models import MainConfig
from mqi_communicator.exceptions import ConfigurationError, ValidationError

T = TypeVar("T")

class ConfigLoader:
    """
    A simple configuration loader that loads a YAML file and maps it to nested dataclasses.
    """

    @staticmethod
    def load_config(path: str) -> MainConfig:
        """
        Loads a configuration file from the given path.

        Args:
            path: The path to the YAML configuration file.

        Returns:
            An instance of MainConfig with the loaded data.

        Raises:
            ConfigurationError: If the file is not found or cannot be parsed.
            ValidationError: If the configuration data is invalid.
        """
        file_path = Path(path)
        if not file_path.is_file():
            raise ConfigurationError(f"Configuration file not found at: {path}")

        try:
            with file_path.open("r") as f:
                raw_config = yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to read or parse YAML file: {e}")

        if not isinstance(raw_config, dict):
            raise ConfigurationError("Configuration file content must be a dictionary.")

        try:
            return ConfigLoader._dict_to_dataclass(MainConfig, raw_config, "root")
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Failed to validate configuration: {e}") from e

    @classmethod
    def _dict_to_dataclass(cls, dclass: Type[T], data: dict, current_path: str) -> T:
        """
        Recursively converts a dictionary to a dataclass instance.
        """
        init_data = {}
        for f in fields(dclass):
            field_path = f"{current_path}.{f.name}"
            if f.name in data:
                field_value = data[f.name]
                if is_dataclass(f.type) and isinstance(field_value, dict):
                    init_data[f.name] = cls._dict_to_dataclass(f.type, field_value, field_path)
                elif isinstance(field_value, f.type):
                    init_data[f.name] = field_value
                else:
                    # Attempt a simple type cast for primitives, e.g. int to float
                    try:
                        init_data[f.name] = f.type(field_value)
                    except (TypeError, ValueError):
                        raise ValidationError(f"Invalid type for field {field_path}. Expected {f.type.__name__}, got {type(field_value).__name__}.")
            elif f.default is MISSING and f.default_factory is MISSING:
                raise ValidationError(f"Missing required configuration field: {field_path}")

        return dclass(**init_data)
