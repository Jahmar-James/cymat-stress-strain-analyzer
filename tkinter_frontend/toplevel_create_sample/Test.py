import os
import sys
import threading
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


print(f"The package name is: {__package__} and module name is: {__name__}")
print(f"Current working directory is:\n{os.getcwd()}\n, Python's system path is:\n {sys.path}")


from configs.managers.tkinter_frontend_workflow_manager import TkinterFrontendWorkflowManager

from .toplevel_create_sample import CreateSampleWindow


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_manager = TkinterFrontendWorkflowManager()
        self.config = (
            self.config_manager.default_config.get("main_window")
            if isinstance(self.config_manager.default_config, dict)
            else {}
        )
        self.title(self.config_manager.default_config.get("title"))
        width = self.config["size"].get("width", 800)
        height = self.config["size"].get("height", 600)

        self.geometry(f"{width}x{height}")

        # Create and place the button in the main window
        open_button = ttk.Button(self, text="Open Toplevel", command=self.open_toplevel)
        open_button.pack(pady=20)

        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.pack(pady=20)

    def open_toplevel(self) -> None:
        defaults = self.config_manager.load_task_config("sample_creation")
        toplevel = CreateSampleWindow(self, submission_callback=handle_data, default_config=defaults)
        toplevel.grab_set()  # Prevent interaction with the main window
        toplevel.wait_window()  # Wait here until the window is destroyed


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
