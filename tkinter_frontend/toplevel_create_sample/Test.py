import os
import sys
import threading
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


print(f"The package name is: {__package__} and module name is: {__name__}")
print(f"Current working directory is:\n{os.getcwd()}\n, Python's system path is:\n {sys.path}")


from configs.managers.tkinter_frontend_workflow_manager import TkinterFrontendWorkflowManager


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_manager = TkinterFrontendWorkflowManager()
        self.config = (
            self.config_manager.default_config.get("main_window")
            if isinstance(self.config_manager.default_config, dict)
            else {}
        )
        self.title(self.config.get("title", "Main Window"))

        # Set initial window size
        width = self.config.get("size", {}).get("width", 800)
        height = self.config.get("size", {}).get("height", 600)
        self.geometry(f"{width}x{height}")

        # Create and place the button in the main window
        open_button = ttk.Button(self, text="Open Toplevel", command=self.open_toplevel)
        open_button.pack(pady=20)
        self.TopLevelButton = open_button

        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.pack(pady=20)

        # Save button to save the current window state
        save_button = ttk.Button(self, text="Save Window State", command=self.save_window_state)
        save_button.pack(pady=20)

        # Load the window state from the last saved file
        load_button = ttk.Button(self, text="Load Window State", command=self.load_window_state)
        load_button.pack(pady=20)

    def open_toplevel(self) -> None:
        from .toplevel_create_sample import CreateSampleWindow

        toplevel = CreateSampleWindow(
            parent=self,
            submission_callback=handle_data,
        )
        toplevel.grab_set()  # Prevent interaction with the main window
        toplevel.wait_window()  # Wait here until the window is destroyed

    def save_window_state(self) -> None:
        """
        Save the current state of the main window (size, position, etc.) to a user-specified file.
        """
        from tkinter.filedialog import asksaveasfilename

        # Testing register a widget state to be saved
        # Should not be saving the button state, but this is just for testing purposes
        # As there it no state to save for a button | other than like disabled or enabled
        self.config_manager.register_widget(
            window_name="main_window",
            widget_id="TopLevelButton",
            widget=self.TopLevelButton,
            widget_type="button",
            var=None,
        )

        # Ask the user for a file name
        import pathlib

        current_directory = pathlib.Path.cwd()
        file_name = asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialfile="user_custom_1.yaml",
            title="Save Window State",
            initialdir=current_directory / self.config_manager._config_directory,
        )

        # If no filename is provided, do not proceed
        if not file_name:
            print("Save operation cancelled.")
            return

        # Call the save method from the config manager
        filename = pathlib.Path(file_name).name
        success = self.config_manager.save_window_state("tkinter_frontend", self, config_name=filename)
        self.config_manager.windows = {}
        self.config_manager.windows[self] = "tkinter_frontend"
        if success:
            print(f"Window state saved successfully to {file_name}.")
        else:
            print(f"Failed to save window state to {file_name}.")

    def load_window_state(self) -> bool:
        """
        Load the window state from a user-specified file and apply it to the main window.
        """
        # Ask the user for a file name
        import pathlib
        from tkinter.filedialog import askopenfilename

        current_directory = pathlib.Path.cwd()
        file_name = askopenfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialfile="user_custom_1.yaml",
            title="Load Window State",
            initialdir=current_directory / self.config_manager._config_directory,
        )

        # If no filename is provided, do not proceed
        if not file_name:
            print("Load operation cancelled.")
            return False

        file_path = pathlib.Path(file_name)
        return self.config_manager.load_window_state(self, file_path)

def handle_data(data) -> None:
    def async_process():
        # Simulate a time-consuming process
        import time

        time.sleep(2)
        print(f"Data processed: {data}")
        print("Async callback complete")

    # Start the asynchronous processing in a new thread
    thread = threading.Thread(target=async_process)
    thread.start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
