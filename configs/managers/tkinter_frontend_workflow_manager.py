from .base_config_manager import BaseConfigManager


class TkinterFrontendWorkflowManager(BaseConfigManager):
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
