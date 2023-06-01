# stress_strain_app.py
import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb

from button_actions import ButtonActions
from data_handler import DataHandler
from plot_manager import PlotManager
from widget_manager import WidgetManager

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
        self.selected_indices = None
        self.selected_specimen_names = []
        self.current_specimen = None
        self.current_slider_manager = None
        # Map tab identifiers to tuples (specimen, slider_manager)
        self.notebook_to_data = {}
        self.export_in_progress = False

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
        self.current_specimen, self.current_slider_manager = self.notebook_to_data.get(
            tab_id, (None, None))


# Run Application
if __name__ == "__main__":
    root = tb.Window( themename= 'darkly')
    app = StressStrainApp(root)
    root.mainloop()

# To Do
# 1. Automate import specimen data from Excel
# - Identify the Excel file format and structure.
# - Use a library like pandas to read the data from the Excel file.
# - Write a function or method to handle the data import and integration with the existing code.

# 2. Fix 2% offset curve
# - Identify the code section responsible for the 2% offset curve calculation.
# - Analyze the code and identify any issues or bugs.
# - Debug and fix the issues to ensure the 2% offset curve is calculated correctly.

# 3. Differentiate between yield shrink and initial yield strength
# - Understand the difference between yield shrink and initial yield strength.
# - Identify the code section where these values are calculated or used.
# - Implement the necessary logic to differentiate between them based on your requirements.

# 4. Add units next to entry Box
# - Identify the entry boxes where units need to be displayed.
# - Update the corresponding labels or widgets to include the appropriate units.

# 5. Refine 1st index and next index
# - Understand the purpose and functionality of the 1st index and next index.
# - Identify the code sections where these values are used or calculated.
# - Make any necessary adjustments or improvements to refine their functionality.

# 6. Be able to create custom Skew cards
# - Determine the requirements and specifications for custom Skew cards.
# - Design a user interface to allow users to create and customize Skew cards.
# - Implement the necessary code to handle the creation and customization of Skew cards.

# 7. Clear specimen func
# - Identify the code section responsible for clearing the current specimen.
# - Add a button or menu option to trigger the "Clear specimen" functionality.
# - Implement the necessary logic to clear the current specimen and reset any associated data or variables.

# 8. re calculate specimen variables
# - Determine the specimen variables that need to be calculated.
# - Identify the relevant formulas or algorithms for the calculations.
# - Implement the necessary code to perform the calculations and update the variables accordingly.

# 9. Refine layout and styling of the GUI
# - Identify the areas of the GUI that require refinement.
# - Modify the existing code or add new code to update the layout and styling as desired.
# - Use appropriate GUI libraries and features to achieve the desired look and feel.

# 10. Ability to shift the stress axes up
# - Identify the code section responsible for the stress axes.
# - Implement the necessary functionality to allow users to shift the stress axes up.
# - Update the corresponding plots or graphs to reflect the shifted stress axes.

# 11. Clean up file name
# - Identify the files or resources with messy or inconsistent names.
# - Rename the files or resources using a consistent and clean naming convention.
# - Update any references to the renamed files in the code.

# 12. Clean up graphs
# - Identify the graphs that require cleaning up.
# - Analyze the code responsible for generating the graphs.
# - Make any necessary adjustments or improvements to enhance the appearance and readability of the graphs.

    # 13. Add Origin line
    # - Identify the code section responsible for plotting the graphs.
    # - Implement the necessary logic to draw an origin line on the graphs.
    # - Update the graph plotting code to include the origin line.

    # 14. Select on unselect lines
    # - Identify the code section or user interface elements related to line selection.
    # - Add the necessary functionality to allow users to select and unselect lines.
    # - Update the code to reflect the selection status of the lines and perform any associated actions accordingly.
