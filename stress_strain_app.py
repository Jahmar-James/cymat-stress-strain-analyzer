# stress_strain_app.py
import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb

from core.button_actions import ButtonActions
from core.data_handler import DataHandler
from core.plot_manager import PlotManager
from core.widget_manager import WidgetManager
import pandas as pd

# To Do
# add cymat icon 

# Main App
class StressStrainApp:
    def __init__(self, master):
        self.master = master
        self.config = AppConfiguration(master)
        self.variables = AppVariables()

        # Initialize instances
        self.data_handler = DataHandler(self)
        self.widget_manager = WidgetManager(self)
        self.button_actions = ButtonActions(self, self.data_handler)
        self.plot_manager = PlotManager(self.widget_manager.notebook, self)

        # Set required instances
        self.data_handler.set_widget_manager(self.widget_manager)
        self.data_handler.set_button_actions(self.button_actions)
        self.widget_manager.set_button_actions(self.button_actions)
        self.button_actions.set_widget_manager(self.widget_manager)
        self.button_actions.set_plot_manager(self.plot_manager)


# app_config,py
class AppConfiguration:
    def __init__(self, master):
        self.master = master
        self.configure_master()

    def configure_master(self):
        # Your existing code for configuring the master window
        self.master.title("Cymat Stress-Strain Analyzer")
        self.master.geometry("850x600")
        self.master.minsize(850, 600)
        self.style = ttk.Style()
        self.style.theme_use('clam')


# app_variables.py
class AppVariables:
    def __init__(self):
        self.specimens = []
        self.average_of_specimens = None
        self.average_of_specimens_hysteresis = pd.DataFrame()
        self.avg_pleatue_stress = None
        self.selected_indices = None
        self.selected_specimen_names = []
        self.current_specimen = None
        self.current_slider_manager = None
        # Map tab identifiers to tuples (specimen, slider_manager)
        self.notebook_to_data = {}
        self.export_in_progress = False
        self.preliminary_sample = False
        self.prelim_mode = tk.BooleanVar(value=self.preliminary_sample)
        self.DIN_Mode = True
        self.ISO_Mode = False

    def add_specimen(self, tab_id, specimen):
        self.specimens.append(specimen)
        # Initialize with no slider manager
        self.notebook_to_data[tab_id] = (specimen, None)

    def set_slider_manager(self, tab_id, slider_manager):
        specimen, _ = self.notebook_to_data.get(tab_id, (None, None))
        if specimen is not None:
            # Update with the new slider manager
            self.notebook_to_data[tab_id] = (specimen, slider_manager)

    def select_tab(self, tab_id):
        self.current_specimen, self.current_slider_manager = self.notebook_to_data.get(tab_id, (None, None))


# Run Application
if __name__ == "__main__":
    root = tb.Window( themename= 'darkly')
    app = StressStrainApp(root)
    root.mainloop()

# To Do
# 5. Refine 1st index and next index
# - Understand the purpose and functionality of the 1st index and next index.
# - Identify the code sections where these values are used or calculated.
# - Make any necessary adjustments or improvements to refine their functionality.

# 10. Ability to shift the stress axes up
# - Identify the code section responsible for the stress axes.
# - Implement the necessary functionality to allow users to shift the stress axes up.
# - Update the corresponding plots or graphs to reflect the shifted stress axes.

# 11. Clean up file name
# - Identify the files or resources with messy or inconsistent names.
# - Rename the files or resources using a consistent and clean naming convention.
# - Update any references to the renamed files in the code.
