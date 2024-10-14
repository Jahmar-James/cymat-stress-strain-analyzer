from pathlib import Path
from typing import Optional
from warnings import warn

import yaml

from utlils.contract_validators import ContractValidators


class BaseConfigManager:
    """
    BaseConfigManager is responsible for managing configuration files in YAML format.
     It provides core functionality for loading, saving, and managing configuration files,
     as well as merging workflow-specific settings with global settings.

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
        self.default_config = {}
        self.task = ""

    def load_config(self, config_name: str = "default") -> dict:
        """
        Load the configuration from the given file.

        Preconditions:
        - `config_name` must correspond to a valid YAML file in the directory.

        Postconditions:
        - Returns a dictionary with configuration data or an empty dictionary if the file doesn't exist.
        """

        # Fatal Check | defualts settings are set correctly
        ContractValidators.validate_directory(
            path=self._config_directory,
            parameter_name="baseworkflow_manger._config_dir",
            function_name="load_workflow_config",
        )

        # Non Fatel Check | if the user defined settings are incorrect just warn the user
        # As the default settings are available as a fallback

        # Try loading from relative path
        relative_config_path = self._get_config_path(self._config_directory, config_name)
        current_directory = Path.cwd()
        config_path = current_directory / relative_config_path
        config = self._read_from_file(config_path)

        if not config:
            # If relative path fails, try loading from an absolute path
            absolute_config_path = Path(f"{config_name}.yaml").resolve()
            config = self._read_from_file(absolute_config_path)

            if not config:
                warn(f"Warning: Workflow config '{config_name}' not found or invalid.")
                return {}

        return config

    def save_config(self, config: dict, config_name: str = "default") -> bool:
        """
        Save the given configuration to the specified file.

        Preconditions:
        - `config` must be a dictionary containing valid configuration data.

        Postconditions:
        - Configuration is saved as a YAML file with the specified `config_name`.
        """
        # Fatal Check | Alert USer and stop execution
        ContractValidators.validate_type(
            value=config,
            expected_types=dict,
            parameter_name="config",
            function_name="save_workflow_config",
        )

        config_file = self._get_config_path(self._config_directory, config_name)
        self._write_to_file(config, config_file)
        return bool(config_file.exists())

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
        if config_name.endswith(".yaml"):
            config_name = config_name.replace(".yaml", "")
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
        print(f"The file {config_file} does not exist.")
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
        # make a bool return type

    # Task-specific (Workflow) methods

    def load_task_config(self, task_name: str, config_name: str) -> dict:
        # Try to load the specific user-configured file first
        user_config = self.load_config(f"{task_name}_{config_name}") if config_name != "defaults" else {}

        # If no user-config exists, fallback to the default config for that task
        default_config = self.load_config(f"{task_name}_defaults") if not user_config else {}

        return self.merge_with_global_settings(user_config, default_config)

    def save_task_config(self, task_name: str, config: dict, config_name: str):
        if "defaults" in config_name:
            warn("Cannot save configuration with 'defaults' in the name. As system defaults are read-only.")
            return False
        return self.save_config(config, f"{task_name}_{config_name}")

    def list_task_configs(self, task_name: str) -> list:
        task_dir = Path(self._config_directory)
        config_files = [f.stem for f in task_dir.glob(f"{task_name}_*.yaml")]
        return config_files

    @staticmethod
    def merge_with_global_settings(workflow_config: dict, global_config: dict) -> dict:
        """
        Merge workflow-specific settings with global settings, where the workflow configuration
        can override the global settings.

        Preconditions:
        - `workflow_config` and `global_config` must be valid dictionaries.

        Postconditions:
        - Returns a dictionary that combines global settings with workflow-specific settings.
        - If a key exists in both configurations, the workflow configuration value will take precedence.
        """

        # ValidationHelper.validate_type(workflow_config, dict, "workflow_config", func_name="merge_with_global_settings")
        # ValidationHelper.validate_type(global_config, dict, "global_config", func_name="merge_with_global_settings")
        return {**global_config, **workflow_config}
