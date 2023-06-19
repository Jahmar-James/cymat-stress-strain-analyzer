# button_actions.py
import tkinter as tk
from typing import Any

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import os
from .plot_manager import draw_error_band_xy, draw_error_band_y

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
    
    def get_export_path():
        pass

    def validate_selected_specimen():
        pass

    def export_data(self) -> None:
        self.data_handler.export_data()

    def export_average_to_excel(self) -> None:
        if self.app.variables.export_in_progress == True:
            tk.messagebox.showerror("Error", "Export is already in progress, ignore the button click.")
            return
        selected_indices = self.app.widget_manager.specimen_listbox.curselection()
        if not selected_indices:
            tk.messagebox.showerror("Error", "No specimens selected for averaging.")
            return
        self.app.data_handler.average_of_selected_specimens(selected_indices)
        if self.app.variables.average_of_specimens is None:
            tk.messagebox.showerror("Error", "No average curve available.")
            return
        
        print("export_average_to_excel")

        file_path = self.widget_manager.get_save_file_path()
        if not file_path:
            return
        
        self.data_handler.export_average_to_excel(selected_indices, file_path)     
        tk.messagebox.showinfo("Data Export", "Data has been exported to Excel successfully!")
        self.app.variables.export_in_progress = False

    def submit(self, event=None) -> None:
        #enter work on submit
        validation_errors = self.data_handler.validate_and_import_data()
    
        if validation_errors:
            tk.messagebox.showerror("Error", validation_errors)
            return

        self.data_handler.import_specimen_data()
        for i in range(1, len(self.widget_manager.data_analysis_buttons)):
            self.widget_manager.data_analysis_buttons[i].config(state='normal')
            self.widget_manager.data_management_buttons[i].config(state='normal')

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
            if  len(selected_specimens) == 1:
                self.data_handler.save_specimen_data(selected_specimens[0], zip_dir)
            else:    
                for specimen in selected_specimens:
                    self.data_handler.save_specimen_data(specimen, zip_dir)   
            
            if zip_dir:   
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
            except Exception as e:
                tk.messagebox.showerror("Import Error", f"Failed to import data from {filename}\n\nError: {e}")

    def export_ms_data(self):
        FILE_TYPE = ( ("All files", "*.*"))
        file_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Document", "*.docx"), ("All files", "*.*")])
        if file_path: 
            selected_indices = self.app.widget_manager.specimen_listbox.curselection()
            if not selected_indices:
                tk.messagebox.showerror("Error", "No specimens selected.")
                return
            try:
                self.data_handler.export_DIN_to_word(selected_indices, file_path)
                tk.messagebox.showinfo("Export Successful", f"Data successfully exported to {file_path}")
            except Exception as e:
                tk.messagebox.showerror("Export Error", f"Failed to export data to {file_path}\n\nError: {e}")
            return
    
    def clear_entries(self) -> None:
        print("clear")
        self.widget_manager.entry_group.clear_entries()  

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
        self.data_handler.update_properties_df(selected_indices)

        tab, _ = self.get_current_tab()
        self.app.plot_manager.master = tab
        self.app.plot_manager.plot_and_draw(
            self.plot_average_and_error_band,
            'Average Stress-Strain Curve',
            'right',
            _
        )
    
    def plot_average_and_error_band(self, ax):
        strain = self.average_of_specimens["strain"].to_numpy()  
        stress = self.average_of_specimens["stress"].to_numpy() 
        std_dev_stress = self.average_of_specimens["std stress"].to_numpy()
        std_dev_strain = self.average_of_specimens["std strain"].to_numpy()
        ax.plot(strain, stress, label="Average Stress-Strain Curve")

        df = self.data_handler.properties_df
        df_summary = self.data_handler.create_summary_df(df)

        Rplt = df_summary.loc['Rplt', 'Average']
        Rplt_E = df_summary.loc['Rplt_E', 'Average']
        Aplt_E = df_summary.loc['Aplt_E', 'Average']
        ReH = df_summary.loc['ReH', 'Average']
        AeH = df_summary.loc['AeH', 'Average']

        # draw_error_band_xy(ax, strain, stress,xerr=std_dev_strain, yerr=std_dev_stress, facecolor="C0", edgecolor="none", alpha=.3)
        draw_error_band_y(ax, strain, stress, err=std_dev_stress, facecolor="C0", edgecolor="none", alpha=.3)

        ax.axhline(y=Rplt, color='r', linestyle='--',linewidth =0.2, label="Rplt")

        # ax.scatter(Aplt_E,Rplt_E, color='g', label="(Aplt_E,Rplt_E)")
        ax.scatter(AeH,ReH,  color='b', label="(ReH, AeH)")

        # ax.annotate("( Aplt_E, Rplt_E)", ( Aplt_E,Rplt_E,), textcoords="offset points", xytext=(-10,10), ha='center')
        ax.annotate("(AeH, ReH)", ( AeH,ReH,), textcoords="offset points", xytext=(-10,10), ha='center')

##### Not implemented ############
    
    def import_properties(self):
        print("Import Specimen Properties button clicked.")
        FILE_TYPE = (("Data files", "*.excel"), ("All files", "*.*"))
        
        file_path = filedialog.askopenfilename(title="Select a data file", filetypes=(FILE_TYPE))
        if file_path:
            try:
                self.data_handler.import_properties(file_path)
                self.widget_manager.update_specimen_listbox(self.app.variables.specimens)
                tk.messagebox.showinfo("Import Successful", f"Data successfully imported from {file_path}")
            except Exception as e:
                tk.messagebox.showerror("Import Error", f"Failed to import data from {file_path}\n\nError: {e}")
            return


    def custom_skew_cards(self):
        print("Custom Skew Cards button clicked.")

    def recalculate_specimen(self):
        print("Recalculate Specimen Variables button clicked.")
        selected_indices = self.widget_manager.specimen_listbox.curselection()
        if not selected_indices:
            tk.messagebox.showerror("caution","All specimen values will be recalculates \n Do you want to continue?")


    def delete_selected_specimens(self):
        """Delete the selected specimens from the list."""
        print("Clear Specimen button clicked.")
        selected_indices = self.widget_manager.specimen_listbox.curselection()
        if not selected_indices:
            tk.messagebox.showerror("Error", "No specimens selected for deletion.")
            return
      
        items_removed = []
        for index in selected_indices:
            items_removed.append(self.app.variables.specimens[index].name)
            self.app.variables.specimens.pop(index)
            self.widget_manager.specimen_listbox.delete(index)
        tk.messagebox.showinfo("Removed", f"{items_removed} specimens removed.")


        #clear note book tab move to other tab
        # update app varable
        # Deal with edge case 1 and 0.
     