import inspect
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from typing import Any, Optional, Type, Union

import customtkinter as ctk

from .base_config_manager import BaseConfigManager

WindowType = Type[Union[tk.Tk, tk.Toplevel, ctk.CTkToplevel, ctk.CTk]]

class TkinterFrontendWorkflowManager(BaseConfigManager):
    """
    Manage the configurations for various Tkinter windows. This manager loads
    and saves window-specific settings, such as size, colors, fonts, and other
    window-specific configurations.

    **Responsibilities**:
    - Load and save Tkinter window configurations. Whioch includes mapping yaml structure to tkinter expected structure.

    Windows (Each application window has a task): ie. Window Name
    - Main window - task: tkinter_frontend
    - Sample creation window - task: sample_creations
    """

    def __init__(self, config_directory="configs/workflows/tkinter"):
        super().__init__(config_directory)
        self.task = "tkinter_frontend"
        self.default_window_config = "tkinter_frontend_defaults"
        # Main window configuration
        self.config_directory = config_directory
        self.default_config = self.load_config(self.default_window_config)
        self.widget_registry = {}
        self.windows = {}

    def load_and_apply_window_default_config(self, window_name: str, window: WindowType) -> dict:
        """
        Set the default configuration for the window.
        """
        default_config = self.load_task_config(window_name, config_name="defaults")

        # Configure the window
        window_config = default_config.get("main_window", {})
        if not self._configure_window(window, window_config, window_name):
            raise ValueError(f"Failed to configure window '{window_name}'.")

        # Return variable initial values
        return default_config

    @staticmethod
    def _restore_registered_widget_states(widget_registry: dict, window_name: str, widget_states: dict) -> bool:
        """
        Restore the state of all registered widgets for the given window.
        """
        if window_name not in widget_registry:
            return False

        success_count = 0
        for widget_id, widget_info in widget_registry[window_name].items():
            var = widget_info.get("var")
            if var is not None and widget_id in widget_states:
                var.set(widget_states[widget_id])
                success_count += 1

        return success_count == len(widget_states)

    def restore_window_state(self, window_name: str, window: WindowType, config_name: str = "user_custom") -> bool:
        """
        Restore the window state from the saved YAML config and apply it to the window and its widgets.
        """
        config = self.load_task_config(window_name, config_name)
        if not config:
            return False

        window_config = config.get("main_window", {})
        # Configure the window
        if not self._configure_window(window, window_config, window_name):
            return False

        # Restore widget states
        return self._restore_registered_widget_states(
            self.widget_registry, window_name, config.get("widget_states", {})
        )

    @staticmethod
    def _configure_window(window: WindowType, config: dict, window_name: str) -> bool:
        """
        Configure the window with the settings from the configuration dictionary.
        """
        if not config:
            return False

        # Handle theme and colors based on light/dark mode
        color_scheme = config.get("color_scheme", "light")
        theme_config = config.get("theme", {})

        if color_scheme == "light":
            light_theme = theme_config.get("light", {})
            foreground_color = light_theme.get("foreground_color", "#000000")  # Default to black
            background_color = light_theme.get("background_color", "#FFFFFF")  # Default to white
            setattr(window, "light_fg_color", foreground_color)
            setattr(window, "light_bg_color", background_color)
        else:  # "dark"
            dark_theme = theme_config.get("dark", {})
            foreground_color = dark_theme.get("foreground_color", "#FFFFFF")  # Default to white
            background_color = dark_theme.get("dark", {}).get("background_color", "#333333")
            setattr(window, "dark_fg_color", foreground_color)
            setattr(window, "dark_bg_color", background_color)
            # Default dark background

        # Apply color configuration
        if isinstance(window, (ctk.CTkToplevel, ctk.CTk)):
            window.configure(fg_color=(foreground_color, background_color))  # CustomTkinter uses fg_color
            ctk.set_appearance_mode(theme_config.get("default", "light"))  # Set default theme
            window.deiconify()

        elif isinstance(window, (tk.Tk, tk.Toplevel)):
            # Tkinter uses bg for background color
            window.configure(bg=background_color)
            # Set Tkinter theme (optional)
            theme_name = theme_config.get("theme_name", "clam")
            setattr(window, "style", ttk.Style())
            window.style.theme_use(theme_name)
        else:
            raise TypeError("Unsupported window type. Expected Tkinter or CustomTkinter window.")

        # Set the title
        title = config.get("title", window_name)
        window.title(title)

        # Apply geometry
        width = config.get("size", {}).get("width", 800)
        height = config.get("size", {}).get("height", 600)
        x_offset = config.get("size", {}).get("x_offset", 100)
        y_offset = config.get("size", {}).get("y_offset", 100)

        geometry = f"{width}x{height}+{x_offset}+{y_offset}"
        window.geometry(geometry)

        # Apply window icon
        icon_path = config.get("icon", None)
        if icon_path:
            window.iconbitmap(icon_path)
            setattr(window, "icon_path", icon_path)  # Store the icon path for saving

        # Resizable window option
        resizable = config.get("resizable", {"width": True, "height": True})
        window.resizable(resizable.get("width", True), resizable.get("height", True))

        # Fullscreen
        fullscreen = config.get("fullscreen", False)
        window.attributes("-fullscreen", fullscreen)

        return True

    @staticmethod
    def _capture_registered_widget_states(widget_registry: dict, window_name: str) -> dict:
        """
        Capture the state of all registered widgets for the given window.
        """
        if window_name not in widget_registry:
            return {}

        widget_states = {}
        for widget_id, widget_info in widget_registry[window_name].items():
            var = widget_info.get("var")
            if var is not None:
                widget_states[widget_id] = var.get()

        return widget_states

    @staticmethod
    def _parse_geometry(geometry: str) -> dict:
        """
        Parse the Tkinter geometry string (e.g., "900x700+200+150") into width, height, x_offset, y_offset.
        """
        dimensions, offsets = geometry.split("+", 1)
        width, height = dimensions.split("x")
        x_offset, y_offset = offsets.split("+")
        return {"width": int(width), "height": int(height), "x_offset": int(x_offset), "y_offset": int(y_offset)}

    def save_window_state(self, window_name: str, window, config_name: str = "user_custom") -> bool:
        """
        Save the current state of the window (geometry, widget values) into a YAML file.
        """
        geometry = window.geometry()
        theme = getattr(window, "theme", None)
        resizable_width = window.resizable()[0]  # Boolean value for width resizability
        resizable_height = window.resizable()[1]  # Boolean value for height resizability
        fullscreen = window.attributes("-fullscreen")
        icon_path = getattr(window, "icon_path", None)

        # Build the configuration dictionary in the required format
        config = {
            "task": window_name,  # Identifying which task or window this configuration is for
            "main_window": {
                "title": window.title(),  # Get the current window title
                "size": self._parse_geometry(geometry),
                "theme": {
                    "default": theme if theme else "light",  # Use the default theme if available
                    "light": {
                        "foreground_color": getattr(window, "light_fg_color", None),
                        "background_color": getattr(window, "light_bg_color", None),
                    },
                    "dark": {
                        "foreground_color": getattr(window, "dark_fg_color", None),
                        "background_color": getattr(window, "dark_bg_color", None),
                    },
                },
                "color_scheme": "dark" if theme == "dark" else "light",  # Set light/dark based on the current theme
                "icon": icon_path,
                "resizable": {"width": resizable_width, "height": resizable_height},
                "fullscreen": fullscreen,
            },
            "widgets": self._capture_registered_widget_states(
                self.widget_registry, window_name
            ),  # Capture widget states
        }

        # Save the configuration to a YAML file
        return self.save_task_config(window_name, config, config_name)

    def load_window_state(self, window: WindowType, config_path: Path) -> bool:
        """
        Load the window state from a YAML configuration file and apply it to the window.
        """
        # Could add a check to unsure the window name is in the config file name
        # Read configuration from the YAML file directly
        config = self._read_from_file(config_path)
        if not config:
            print(f"Error: Unable to load configuration from {config_path}")
            return False

        # Extract the main window configuration
        window_config = config.get("main_window", {})
        if not window_config:
            print(f"Error: 'main_window' section missing in config '{config_path.name}'.")
            return False

        # Apply the configuration to the window
        if not self._configure_window(window, window_config, window_name=config.get("task", "window")):
            print(f"Error: Failed to configure window from '{config_path.name}'.")
            return False

        # Restore widget states (optional)
        widget_states = config.get("widgets", {})
        if widget_states:
            if not self._restore_registered_widget_states(
                self.widget_registry, config.get("task", "window"), widget_states
            ):
                print(f"Warning: Failed to restore some widget states for window '{config.get('task', 'window')}'.")

        return True

    def register_widget(self, window_name: str, widget_id: str, widget, widget_type: str, var: Any) -> bool:
        """
        Register a widget variable to be saved and restored with the window state.
        """
        if window_name not in self.widget_registry:
            self.widget_registry[window_name] = {}

        self.widget_registry[window_name][widget_id] = {
            "widget": widget,
            "type": widget_type,
            "var": var,
        }

        return bool(widget_id in self.widget_registry[window_name])

    @staticmethod
    def _get_variable_name(var) -> str:
        """
        Use reflection to get the variable name from the calling scope.
        This ensures that the widget ID matches the variable name.
        """
        # Get the current stack frame and inspect the local variables
        frame = inspect.currentframe()
        try:
            outer_frame = frame.f_back.f_back  # Step back to the function that called this method
            local_vars = outer_frame.f_locals
            for var_name, var_value in local_vars.items():
                if var_value is var:
                    return var_name
        finally:
            del frame  # Clean up the reference to the frame to avoid memory leaks
        return ""

    def auto_register_widget(self, window_name: str, widget, var=None) -> bool:
        """
        Automatically register a widget by using the variable's name as the widget ID.
        If a variable is provided, its name is extracted using reflection.
        """
        if var is not None:
            # Extract the variable's name using reflection
            var_name = self._get_variable_name(var)
            if var_name:
                return self.register_widget(window_name, widget, var_name, widget_type="auto", var=var)
            else:
                raise ValueError("Failed to extract variable name for widget.")
        else:
            raise ValueError("No Tkinter variable provided for widget registration.")
