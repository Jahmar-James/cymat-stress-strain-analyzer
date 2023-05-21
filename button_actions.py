# button_actions.py
import tkinter as tk
from typing import Any

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import os

class ButtonActions:
    def __init__(self, app: Any, data_handler: Any) -> None:
        self.app = app
        self.data_handler = data_handler
    
    def set_widget_manager(self, widget_manager: Any) -> None:
        self.widget_manager = widget_manager

    def set_plot_manager(self, plot_manager: Any) -> None:
        self.plot_manager = plot_manager
    
    @property
    def specimens(self):
        return self.app.variables.specimens

    @property
    def average_of_specimens(self):
        return self.app.variables.average_of_specimens

    def export_data(self) -> None:
        self.data_handler.export_data()

    def export_average_to_excel(self) -> None:
        self.data_handler.export_average_to_excel()

    def submit(self) -> None:
        #enter work on submit
        validation_errors = self.data_handler.validate_and_import_data()
    
        if validation_errors:
            tk.messagebox.showerror("Error", validation_errors)
            return

        self.data_handler.import_specimen_data()
        for i in range(1, len(self.widget_manager.buttons)):
            self.widget_manager.buttons[i].config(state='normal')

    def save_selected_specimens(self) -> None:
        selected_specimens = self.data_handler.get_selected_specimens()
        if not selected_specimens:
            tk.messagebox.showerror("Error", "No specimens selected for saving.")
            return
        
        # Ask the user where to save the zip file
        while True:
            zip_dir = filedialog.askdirectory()
            if not zip_dir.startswith(os.path.abspath('exported_data')):
                break
            tk.messagebox.showerror("Invalid Directory", "Please select a directory other than 'exported_data'")
        try:
            for specimen in selected_specimens:
                self.data_handler.save_specimen_data(specimen, zip_dir)
            tk.messagebox.showinfo("Save Successful", f"Saved selected specimens.")
        except Exception as e:
            tk.messagebox.showerror("Save Error", f"Failed to save selected specimens.\n\nError: {e}")

    def import_data(self) -> None:
        DAT_FILE_TYPE = (("Data files", "*.zip"), ("All files", "*.*"))
        file_path = filedialog.askopenfilename(title="Select a data file", filetypes=(DAT_FILE_TYPE))
        if file_path:
            filename = Path(file_path).name
            try:
                self.data_handler.load_specimen_data(file_path)
                tk.messagebox.showinfo("Import Successful", f"Imported data from {filename}")
            except Exception as e:
                tk.messagebox.showerror("Import Error", f"Failed to import data from {filename}\n\nError: {e}")

    
    def clear_entries(self) -> None:
        self.widget_manager.name_entry.delete(0, 'end')
        self.widget_manager.length_entry.delete(0, 'end')
        self.widget_manager.width_entry.delete(0, 'end')
        self.widget_manager.thickness_entry.delete(0, 'end')
        self.widget_manager.weight_entry.delete(0, 'end')

    def get_current_tab(self):
        current_tab_id = self.widget_manager.notebook.select()
        self.app.variables.select_tab(current_tab_id)
        current_specimen = self.app.variables.current_specimen
        return current_tab_id, current_specimen
    
    def plot_current_specimen(self) -> None:
        tab, specimen = self.get_current_tab()
        self.app.plot_manager.master = tab
        self.app.plot_manager.plot_and_draw(
            specimen.plot_curves,
            f"Stress-Strain Curve for {specimen.name}",
            'left',
            specimen
        )

    def plot_all_specimens(self) -> None:
        def plot_function(ax):
            for specimen in self.specimens:
                specimen.plot_stress_strain(ax)

        tab, current_specimen = self.get_current_tab()
        self.app.plot_manager.master = tab
        self.app.plot_manager.plot_and_draw(
            plot_function,
            "Overlay of all specimens",
            'middle',
            current_specimen
        )

    def plot_average(self) -> None:
        selected_indices = self.widget_manager.specimen_listbox.curselection()
        if not selected_indices:
            tk.messagebox.showerror("Error", "No specimens selected for averaging.")
            return
        
        self.data_handler.average_of_selected_specimens(selected_indices)

        tab, _ = self.get_current_tab()
        self.app.plot_manager.master = tab
        self.app.plot_manager.plot_and_draw(
            lambda ax: ax.plot(self.average_of_specimens["strain"], self.average_of_specimens["stress"], label="Average Stress-Strain Curve"),
            'Average Stress-Strain Curve',
            'right',
            _
        )


##### Not implemented ############

    def delete_selected_specimens(self):
        """Delete the selected specimens from the list."""
        selected_indices = self.widget_manager.specimen_listbox.curselection()
        if not selected_indices:
            tk.messagebox.showerror("Error", "No specimens selected for deletion.")
            return

        for index in selected_indices:
            self.app.variables.specimens.pop(index)

        self.widget_manager.populate_specimen_listbox()
