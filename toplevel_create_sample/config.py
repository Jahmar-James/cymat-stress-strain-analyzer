from abc import ABC, abstractmethod
from pathlib import Path

import yaml


class ConfigLoaderBase(ABC):
    def __init__(self, config_directory):
        self._config_directory = Path(config_directory)
        self._config_directory.mkdir(exist_ok=True)

    @abstractmethod
    def load_config(self, config_name="default") -> dict:
        """Abstract method to load configuration. To be implemented by subclasses."""
        pass

    @abstractmethod
    def save_config(self, config, config_name="default") -> None:
        """Abstract method to save configuration. To be implemented by subclasses."""
        pass

    @staticmethod
    def _get_config_path(config_directory, config_name) -> Path:
        """Static method to get the full path for a specific configuration file."""
        return Path(config_directory) / f"{config_name}.yaml"

    @staticmethod
    def _read_from_file(config_file) -> dict:
        """Static method to read YAML configuration from a file."""
        if config_file.exists():
            try:
                with config_file.open("r") as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error reading YAML file: {e}")
        return None

    @staticmethod
    def _write_to_file(config, config_file):
        """Static method to write configuration to a YAML file."""
        with config_file.open("w") as f:
            yaml.dump(config, f)


class AppSettings(ConfigLoaderBase):
    def __init__(self, config_directory="configurations/app", defaults=None):
        """
        Initialize with optional defaults provided by frontend components.
        """
        super().__init__(config_directory)
        self._default_app_config = defaults if defaults else {"theme": "light", "font_size": 12, "notifications": True}

    def load_config(self, config_name="default") -> dict:
        config_file = self._get_config_path(self._config_directory, config_name)
        user_config = self._read_from_file(config_file)
        return {**self._default_app_config, **(user_config or {})}

    def save_config(self, config, config_name="default") -> None:
        config_file = self._get_config_path(self._config_directory, config_name)
        self._write_to_file(config, config_file)


class WorkflowSettings(ConfigLoaderBase):
    def __init__(self, config_directory="configurations/workflows"):
        super().__init__(config_directory)

    def load_config(self, config_name="default") -> dict:
        config_file = self._get_config_path(self._config_directory, config_name)
        return self._read_from_file(config_file)

    def save_config(self, config, config_name="default") -> None:
        config_file = self._get_config_path(self._config_directory, config_name)
        self._write_to_file(config, config_file)
        self._write_to_file(config, config_file)
