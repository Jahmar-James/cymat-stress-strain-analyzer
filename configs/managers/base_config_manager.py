from abc import ABC, abstractmethod
from pathlib import Path
from warnings import warn

import yaml


class BaseConfigManager(ABC):
    """
    BaseConfigManager is an abstract class for managing configuration files in YAML format.
    It provides core functionality for reading from and writing to configuration files
    and can be extended by specific configuration managers.

    **Responsibilities**:
    - Load configuration files from a specified directory.
    - Save configuration files to a specified directory.
    - Handle directory creation if necessary.

    **Assumptions**:
    - The directory structure where configurations are stored will remain static after initialization.
    - YAML files will be used for all configurations.
    - Validators are selectively applied only in higher-level API methods to enforce valid inputs.
    - Lower-level methods (e.g., _read_from_file) assume validation has already occurred.

    **Preconditions**:
    - Subclasses must implement `load_config` and `save_config`.

    **Postconditions**:
    - When `save_config` is called, the configuration will be written to the correct file.
    - When `load_config` is called, it will return the configuration data, or an empty dict if the file doesn't exist.
    """

    def __init__(self, config_directory: str):
        """
        Initialize the configuration manager with the directory where configuration files are stored.

        Preconditions:
        - `config_directory` must be a valid directory path.

        Postconditions:
        - The directory will be created if it does not exist.
        """
        self._config_directory = Path(config_directory)
        self._config_directory.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def load_config(self, config_name: str = "default") -> dict:
        """
        Load the configuration from the given file.

        Preconditions:
        - `config_name` must correspond to a valid YAML file in the directory.

        Postconditions:
        - Returns a dictionary with configuration data or an empty dictionary if the file doesn't exist.
        """
        pass

    @abstractmethod
    def save_config(self, config: dict, config_name: str = "default") -> None:
        """
        Save the given configuration to the specified file.

        Preconditions:
        - `config` must be a dictionary containing valid configuration data.

        Postconditions:
        - Configuration is saved as a YAML file with the specified `config_name`.
        """
        pass

    @staticmethod
    def _get_config_path(config_directory: Path, config_name: str) -> Path:
        """
        Generate the file path for the configuration based on its name.

        Preconditions:
        - `config_directory` must be a valid Path object.
        - `config_name` must be a valid filename (without the extension).

        Postconditions:
        - Returns the full path to the YAML configuration file.
        """
        return config_directory / f"{config_name}.yaml"

    @staticmethod
    def _read_from_file(config_file: Path) -> dict:
        """
        Read and parse a YAML configuration file.

        Preconditions:
        - `config_file` must be a valid Path object pointing to a YAML file.

        Postconditions:
        - Returns a dictionary with the parsed data or an empty dictionary if the file does not exist or is invalid.
        """
        if config_file.exists():
            try:
                with config_file.open("r") as file:
                    return yaml.safe_load(file) or {}
            except yaml.YAMLError:
                warn(f"Error reading YAML file: {config_file}")
        return {}

    @staticmethod
    def _write_to_file(config: dict, config_file: Path) -> None:
        """
        Write the configuration data to a YAML file.

        Preconditions:
        - `config` must be a dictionary with serializable data.
        - `config_file` must be a valid Path object pointing to a writable location.

        Postconditions:
        - The configuration will be written to the specified YAML file.
        """
        with config_file.open("w") as file:
            yaml.dump(config, file)
