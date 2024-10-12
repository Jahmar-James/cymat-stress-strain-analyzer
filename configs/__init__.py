"""
Overview of the Configurations Module

/configs - Configuration Management for the Application

This folder contains the configuration management system for handling global settings,
workflow settings, and task-specific configurations across the application.

## Structure Overview

The configuration system is centered around a single class:

1. **BaseConfigManager** (Handles both global and task-specific configurations):
    - This class is responsible for managing configuration files in YAML format.
      It provides core functionality for reading, saving, and merging configurations.
    - **Purpose**: To load, save, and manage reusable configurations that may apply globally or to specific tasks.
    - **Features**:
        - Loading and saving configuration files in YAML format.
        - Merging task-specific settings with global settings.
        - Preventing modifications to default configurations.

## Class Summary:

### BaseConfigManager (configurations/managers/base_config_manager.py)
- **Purpose**: Centralized class for managing configurations. Handles both global settings and task-specific settings for workflows (e.g., plotting, sample creation).
- **Key Features**:
    - Load and save YAML configurations.
    - Merge workflow-specific settings with global settings.
    - List available configurations for tasks.
    - Prevent saving of default configurations to ensure system defaults remain read-only.

## Class Methods:

### load_config (config_name: str = "default") -> dict
- **Purpose**: Load a configuration file in YAML format.
- **Returns**: A dictionary containing the configuration, or an empty dictionary if the file doesn't exist.
- **Example**:
    ```python
    global_config = config_manager.load_config("global_settings")
    ```

### save_config (config: dict, config_name: str = "default") -> bool
- **Purpose**: Save a configuration dictionary to a specified file.
- **Returns**: True if the configuration is successfully saved.
- **Example**:
    ```python
    config_manager.save_config(global_config, "global_settings")
    ```

### load_task_config (task_name: str, config_name: str = "default") -> dict
- **Purpose**: Load a task-specific configuration. Attempts to load user-defined settings first, falling back to default settings if they exist.
- **Returns**: A merged dictionary where the task-specific configuration overrides global defaults.
- **Example**:
    ```python
    sample_creation_config = config_manager.load_task_config("sample_creation")
    ```

### save_task_config (task_name: str, config: dict, config_name: str) -> bool
- **Purpose**: Save task-specific configurations. Prevents modifications to system default configurations.
- **Returns**: True if the configuration is successfully saved. Will return False and raise a warning if attempting to save a default configuration.
- **Example**:
    ```python
    config_manager.save_task_config("sample_creation", config, "user_custom")
    ```

### list_task_configs (task_name: str) -> list
- **Purpose**: List all available configuration files for a specific task.
- **Returns**: A list of configuration file names for the task.
- **Example**:
    ```python
    available_configs = config_manager.list_task_configs("plotting")
    ```

### merge_with_global_settings (workflow_config: dict, global_config: dict) -> dict
- **Purpose**: Merge workflow-specific settings with global settings, where workflow settings take precedence.
- **Returns**: A dictionary that combines both global and workflow-specific settings, giving precedence to the workflow settings.
- **Example**:
    ```python
    merged_config = config_manager.merge_with_global_settings(workflow_config, global_config)
    ```

## Configuration Management Strategy:

- **Global Configurations**: Settings that apply application-wide, such as theme, default environment conditions, or UI preferences.
    - These are typically loaded and managed by loading files such as `global_settings.yaml`.
- **Task-Specific Configurations**: Settings that apply only to specific workflows, such as sample creation defaults or plotting preferences.
    - These are managed by loading files with task-specific names, like `sample_creation_defaults.yaml` or `plotting_user_custom.yaml`.

## Extending the System:

- To add new workflows, extend the system by creating YAML configuration files specific to that task.
- When you need custom logic around workflows (e.g., merging configurations), utilize the `BaseConfigManager` to handle file loading, saving, and merging.
"""
