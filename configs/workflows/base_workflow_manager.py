from warnings import warn

from configs.managers.base_config_manager import BaseConfigManager


class BaseWorkflowManager(BaseConfigManager):
    """
    BaseWorkflowManager is an abstract class designed for managing task-specific workflow configurations.
    It extends BaseConfigManager to handle loading, saving, and merging of workflow configurations with
    global settings. Workflow managers that inherit from this class can define specific behaviors for
    tasks like plotting, sample creation, etc.

    **Responsibilities**:
    - Load and save workflow-specific configurations.
    - Merge global settings with workflow-specific settings.
    - Provide extensibility for task-oriented workflows (e.g., plotting workflows, sample creation workflows).

    **Assumptions**:
    - Workflow-specific configurations may override global settings if necessary.
    - Global settings are loaded separately and passed as an argument for merging.

    **Preconditions**:
    - Subclasses must implement `load_config` and `save_config` as per their specific needs.

    **Postconditions**:
    - The workflow-specific settings will be loaded, saved, and merged with global defaults where applicable.
    """

    def __init__(self, config_directory: str):
        """
        Initialize the workflow manager with the directory where workflow configurations are stored.

        Preconditions:
        - `config_directory` must be a valid directory path.

        Postconditions:
        - The directory will be created if it does not exist.
        """
        super().__init__(config_directory)

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
        ValidationHelper.validate_type(workflow_config, dict, "workflow_config", func_name="merge_with_global_settings")
        ValidationHelper.validate_type(global_config, dict, "global_config", func_name="merge_with_global_settings")
        return {**global_config, **workflow_config}

    def load_workflow_config(self, config_name: str = "default") -> dict:
        """
        Load the workflow-specific configuration from a YAML file.

        Preconditions:
        - `config_name` must correspond to a valid YAML file in the directory.

        Postconditions:
        - Returns a dictionary with workflow-specific configuration data, or an empty dictionary
          if the file does not exist.
        """
        config_file = self._get_config_path(self._config_directory, config_name)
        config = self._read_from_file(config_file)
        if not config:
            warn(f"Warning: Workflow config '{config_name}' not found or invalid.")
        return config

    def save_workflow_config(self, config: dict, config_name: str = "default") -> None:
        """
        Save the workflow-specific configuration to a YAML file.

        Preconditions:
        - `config` must be a dictionary containing valid configuration data.

        Postconditions:
        - The configuration will be saved to the specified YAML file.
        """
        ValidationHelper.validate_type(config, dict, "config", func_name="save_workflow_config")
        config_file = self._get_config_path(self._config_directory, config_name)
        self._write_to_file(config, config_file)
        self._write_to_file(config, config_file)
        self._write_to_file(config, config_file)
        self._write_to_file(config, config_file)
