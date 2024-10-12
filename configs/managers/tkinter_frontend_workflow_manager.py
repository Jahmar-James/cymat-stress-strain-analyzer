from .base_workflow_manager import BaseWorkflowManager


class TkinterFrontendWorkflowManager(BaseWorkflowManager):
    """
    Manage the configurations for various Tkinter windows. This manager loads
    and saves window-specific settings, such as size, colors, fonts, and other
    window-specific configurations.

    This manager supports multiple Tkinter windows by pointing to the correct
    configuration file based on the window name.
    """

    def __init__(self, config_directory="configs/workflows/tkinter"):
        super().__init__(config_directory)
        self.task = "tkinter"
        self.default_window_config = "tkinter_frontend_defaults"
        self.default_config = self.load_config(self.default_window_config)


# class SampleCreationWorkflowManager(BaseWorkflowManager):
#     def __init__(self, config_directory="configurations/workflows/tkinter"):
#         super().__init__(config_directory)
#         self.default_config = self.load_config("default")
#         self.task = "sample_creation"

#     # Sample creation-specific logic can be added here
#     def create_sample(self, config_name="default"):
#         config = self.list_task_configs("sample_creation")
#         # Use the loaded config to guide sample creation
#         print(f"Creating sample with config: {config}")


# class PlottingWorkflowManager(BaseWorkflowManager):
#     def __init__(self, config_directory="configurations/workflows/plotting"):
#         super().__init__(config_directory)
#         self.default_config = self.load_config("default")

#     # You can add plotting-specific methods here
#     def generate_plot(self, data, config_name="default"):
#         config = self.list_task_configs("plotting")
#         # Use the loaded config to generate a plot
#         print(f"Generating plot with config: {config}")
