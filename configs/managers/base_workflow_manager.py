from warnings import warn

from configs.managers.base_config_manager import BaseConfigManager
from utlils.contract_validators import ContractValidators


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
        self.default_config = {}

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

    def load_task_config(self, task_name: str, config_name: str = "defaults") -> dict:
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
