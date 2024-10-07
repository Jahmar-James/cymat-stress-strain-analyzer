"""
Overview of the Configurations Module

/configs - Configuration Management for the Application

This folder contains the configuration management system for handling global settings,
workflow settings, and task-specific configurations across the application.

## Structure Overview

The config system is divided into two main components:

1. **Config Managers** (Static, predefined settings):
    - These classes are responsible for managing default configurations that rarely change
      (e.g., global app settings, default uncertainty values).
    - **Purpose**: To load, save, and manage reusable, global configurations.
    - **Examples**:
        - `GlobalAppConfigManager`: Manages global settings such as environmental conditions,
          machine settings, and general app behavior.
        - `UncertaintyConfigManager`: Manages default uncertainty settings for various test measurements.
        - `TestConfigManager`: Manages configuration related to mechanical test setups that don't change frequently.

2. **Workflow Managers** (Task-oriented configurations):
    - These classes handle configurations for specific tasks or processes within the application.
    - **Purpose**: To allow dynamic, task-specific behavior that can override global settings
      based on the current workflow.
    - **Examples**:
        - `PlottingWorkflowManager`: Defines how plots should be generated (e.g., axes, colors, line styles).
        - `SampleCreationWorkflowManager`: Manages sample creation defaults, such as physical properties of samples.
        - `FrontendWorkflowManager`: Manages frontend behaviors like window layouts or UI preferences.

## Class Summaries:

### BaseConfigManager (configurations/managers/base_config_manager.py)
- **Purpose**: Base class that provides common functionality for loading and saving configurations.
  Used by all config and workflow managers.
- **Key Features**:
    - Load and save YAML configurations.
    - Standardized methods for handling config files.

### GlobalAppConfigManager (configurations/managers/global_app_config_manager.py)
- **Purpose**: Manages global application settings, including environmental conditions and machine setup.
- **Use Case**: Load the default settings for environmental conditions (e.g., temperature, humidity)
  or machine-specific information like load cell calibration.
- **Example Settings**:
    - `environmental_conditions`: {"temperature": 23, "humidity": 50}
    - `machine_settings`: {"load_cell_calibration": "2024-01-01", "operator_name": "John Doe"}

### UncertaintyConfigManager (configurations/managers/uncertainty_config_manager.py)
- **Purpose**: Manages default uncertainty settings, such as for force, displacement, and other test measurements.
- **Use Case**: Load default uncertainties that apply to measurements in the testing process,
  allowing users to override them if needed.
- **Example Settings**:
    - `force_uncertainty`: {"value": "±0.5%", "type": "relative"}
    - `displacement_uncertainty`: {"value": 0.01, "type": "absolute"}

### TestConfigManager (configurations/managers/test_config_manager.py)
- **Purpose**: Manages configuration related to mechanical test setups that remain relatively constant.
- **Use Case**: Load predefined test settings like test speed, ramp times, and pre-test conditions.
- **Example Settings**:
    - `test_speed`: 5  # mm/min
    - `ramp_time`: 10  # seconds

### BaseWorkflowManager (configurations/workflows/base_workflow_manager.py)
- **Purpose**: Provides a base class for all workflow managers. It adds task-oriented behavior on top of
  `BaseConfigManager` and allows merging/overriding global settings with task-specific configurations.
- **Key Features**:
    - Merging workflow-specific settings with global defaults.
    - Shared functionality for task-specific workflows (e.g., plotting, sample creation).

### PlottingWorkflowManager (configurations/workflows/plotting_workflow_manager.py)
- **Purpose**: Manages configurations related to plotting tasks. Allows users to define how they want
  plots to be generated (e.g., line colors, axes).
- **Use Case**: Customize plot appearance and behavior for each test or analysis session.
- **Example Settings**:
    - `line_color`: "blue"
    - `x_axis_label`: "Time (s)"
    - `y_axis_label`: "Force (N)"

### SampleCreationWorkflowManager (configurations/workflows/sample_creation_workflow_manager.py)
- **Purpose**: Manages the default behavior for creating sample entities, including physical properties
  like length, width, thickness, and material.
- **Use Case**: Load predefined sample creation workflows to reduce repetitive input when defining samples.
- **Example Settings**:
    - `default_length`: 10.0  # mm
    - `default_thickness`: 0.5  # mm
    - `default_material`: "steel"

### FrontendWorkflowManager (configurations/workflows/frontend_workflow_manager.py)
- **Purpose**: Manages configurations related to the user interface, such as window layouts and
  UI component behavior.
- **Use Case**: Configure how a `Tkinter` window or any other frontend component is laid out,
  including buttons, menus, and interactions.
- **Example Settings**:
    - `main_window_size`: {"width": 800, "height": 600}
    - `toplevel_window_layout`: {"position": "center"}

## General Guidelines for Extending:

- **Add New Workflow Managers**: When adding new workflows, extend `BaseWorkflowManager` to inherit
  common behavior. This ensures consistent management of workflow-specific settings.
- **Add New Config Managers**: When creating new config managers for global settings, extend `BaseConfigManager`.
- **Separation of Concerns**: Keep config managers focused on static, reusable settings and workflows
  focused on task-specific processes that might override global settings.
"""
