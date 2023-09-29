# button_actions.py
import tkinter as tk
from typing import Any

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import os
from .plot_manager import draw_error_band_xy, draw_error_band_y, draw_error_band_y_modified
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np

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
    
    @property
    def average_of_specimens_hysteresis(self):
        return self.app.variables.average_of_specimens_hysteresis
    
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
    
        if self.app.variables.average_of_specimens is None:
            self.app.data_handler.average_of_selected_specimens(selected_indices)
            if self.app.variables.average_of_specimens.empty:
                tk.messagebox.showerror("Error", "No average curve available.")
                return
             
        print("export_average_to_excel")

        file_path = self.widget_manager.get_save_file_path()
        if not file_path:
            return
        
        self.data_handler.export_average_to_excel(selected_indices, file_path)   
  
        tk.messagebox.showinfo("Data Export", "Data is getting exported to Excel, please wait...")

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
        title = f"Stress-Strain Curve for {specimen.name}"

        if self.widget_manager.plot_title_entry_group.entries[0].get() ==  self.widget_manager.plot_title_entry_group.entries[0].placeholder or self.widget_manager.plot_title_entry_group.entries[0].get() == "":
            title = f"Stress-Strain Curve for {specimen.name}"
        else:
            self.widget_manager.plot_title_entry_group.entries[0].get().encode('utf-8').decode('unicode_escape')

        self.app.plot_manager.plot_and_draw(
            specimen.plot_curves,
            title,
            'left',
            specimen
        )

    def plot_all_specimens(self) -> None:
        def plot_function(ax):
            for specimen in self.specimens:
                specimen.plot_stress_strain(ax)

        tab, current_specimen = self.get_current_tab()
        self.app.plot_manager.master = tab

        title = "Specimens Overlayed"

        if self.widget_manager.plot_title_entry_group.entries[1].get() ==  self.widget_manager.plot_title_entry_group.entries[1].placeholder or self.widget_manager.plot_title_entry_group.entries[1].get() == "":
            title = "Specimens Overlayed"
        else:
            title = self.widget_manager.plot_title_entry_group.entries[1].get().encode('utf-8').decode('unicode_escape')
        
        self.app.plot_manager.plot_and_draw(
            plot_function,
            title, 
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

        title = 'Average Stress-Strain Curve'

        if self.widget_manager.plot_title_entry_group.entries[2].get() ==  self.widget_manager.plot_title_entry_group.entries[1].placeholder or self.widget_manager.plot_title_entry_group.entries[2].get() == "":
            title = 'Average Stress-Strain Curve'
        else:
            title = self.widget_manager.plot_title_entry_group.entries[2].get().encode('utf-8').decode('unicode_escape')

        self.app.plot_manager.plot_and_draw(
            self.plot_average_and_error_band,
            title,
            'right',
            _
        )
    
    def plot_average_and_error_band(self, ax): ############################################# SET to FALSE for external ploting
        strain = self.average_of_specimens["Strain"].to_numpy()  
        stress = self.average_of_specimens["Stress"].to_numpy()
        ax.plot(strain, stress, label="Average Stress-Strain Curve") 

        if self.average_of_specimens_hysteresis.empty == False:
            self.plot_average_hysteresis(ax)

        internal_plot = self.widget_manager.internal_plot_enabled.get()
        external_plot = self.widget_manager.external_plot_enabled.get()
        
        std_dev_stress = self.average_of_specimens["std Stress"].to_numpy()
        std_dev_strain = self.average_of_specimens["std Strain"].to_numpy()

        if internal_plot == True or external_plot == True:
            # plot the error band based on the std dev of the stress and strain
            draw_error_band_y(ax, strain, stress, err=std_dev_stress, facecolor="C0", edgecolor="none", alpha=.3)

        if not internal_plot and not external_plot:

            draw_error_band_y(ax, strain, stress, err=std_dev_stress, facecolor="C0", edgecolor="none", alpha=.3)
            # draw_error_band_xy(ax, strain, stress,xerr=std_dev_strain, yerr=std_dev_stress, facecolor="C0", edgecolor="none", alpha=.3)

            max_stress = self.average_of_specimens["max Stress"].to_numpy()
            min_stress = self.average_of_specimens["min Stress"].to_numpy()
            
            draw_error_band_y_modified(ax, strain, max_stress, min_stress, facecolor="C3", edgecolor="none", alpha=.3)
            ucl = self.average_of_specimens["UCL Stress"].to_numpy()
            lcl = self.average_of_specimens["LCL Stress"].to_numpy()

            # self.plot_control_limits(ax, ucl, lcl, strain)
    
        #Add Module line and strength points
        df_summary = self.data_handler.create_summary_df(self.data_handler.properties_df)
        self.data_handler.calculate_avg_KPI(lower_strain = 0.2, upper_strain = 0.4)
        # print Energy values for use they dont need to be exported to excel
        dense_strain = strain[self.app.variables.average_plt_end_id]
        dense_stress = stress[self.app.variables.average_plt_end_id]
        self.display_energy_values(df_summary, dense_strain)
        self.display_key_strain_values(stress, strain, dense_stress)

        if self.app.variables.average_plt:
             plt = self.app.variables.average_plt
             ax.axhline(y=plt, color='orange', linestyle='--', label=f"Plateau Stress: ({plt:.1f} MPa)")
        if  self.app.variables.average_plt_end_id:
             plt_end = self.average_of_specimens["Stress"].to_numpy()[self.app.variables.average_plt_end_id]
            #  ax.axhline(y=plt_end, color='r', linestyle='--', label=f"Plateau Stress End: {plt_end:.2f} Mpa")
             ax.scatter(dense_strain, plt_end, color='r', marker='^', s=50, label=f"Densification Strain ({dense_strain*100:.1f} %)")
            #  ax.annotate(f"Densification Strain ({dense_strain*100:.1f} %)", (dense_strain, plt_end), xytext=(dense_strain+0.01, plt_end+0.01), arrowprops=dict(facecolor='black', shrink=0.05))

        self.app.variables.DIN_Mode = False

        if self.app.variables.DIN_Mode  == True:
            Rplt = df_summary.loc['Rplt', 'Average']
            Rplt_E = df_summary.loc['Rplt_E', 'Average']
            ax.axhline(y=Rplt, color='r', linestyle='--', label="Plt")

            ax.scatter(Aplt_E,Rplt_E, color='g', label="(Aplt_E,Rplt_E)")
            ax.scatter(AeH,ReH,  color='b', label="(ReH, AeH)")

            ax.annotate("( Aplt_E, Rplt_E)", ( Aplt_E,Rplt_E,), textcoords="offset points", xytext=(-10,10), ha='center')
            ax.annotate("(AeH, ReH)", ( AeH,ReH,), textcoords="offset points", xytext=(-10,10), ha='center')


    def display_energy_values(self, df_summary, dense_strain = "N/A"):

        density = df_summary.loc['density', 'Average']  # g/cm^3
        density_kg_meters = density * 1000  # kg/m^3

        # calculate energy data and round to 2 decimal places for readability
        E20_kJ_m3 = round(self.app.variables.average_E20 * 1000, 2)
        E20_kJ_kg = round((self.app.variables.average_E20 * 1000) / density_kg_meters, 2)

        E50_kJ_m3 = round(self.app.variables.average_E50 * 1000, 2)
        E50_kJ_kg = round((self.app.variables.average_E50 * 1000) / density_kg_meters, 2)

        E_dense_kJ_m3 = round(self.app.variables.average_E_dense * 1000, 2)
        E_dense_kJ_kg = round((self.app.variables.average_E_dense * 1000) / density_kg_meters, 2)

        # prepare data to display in tabulated form
        energy_data = [
            ["20 %", f"{E20_kJ_m3} kJ/m^3", f"{E20_kJ_kg} kJ/kg"],
            ["50 %", f"{E50_kJ_m3} kJ/m^3", f"{E50_kJ_kg} kJ/kg"],
            [f"Densification {dense_strain*100:.1f} %", f"{E_dense_kJ_m3} kJ/m^3", f"{E_dense_kJ_kg} kJ/kg"]
        ]

        headers = ["Energy (%)", "Energy (kJ/m^3)", "Specific Energy (kJ/kg)"]

        print("\nEnergy Values:")
        print(tabulate(energy_data, headers, tablefmt="grid"))

    def display_key_strain_values(self, stress, strain, dense_stress = "N/A"):
        # calculate stress at key strian values and round to 2 decimal places for readability
        # key strain values are 20%, 50%, and densification strain

        # Find the closest stress values for the key strain values
        stress_20 = round(stress[np.abs(strain - 0.20).argmin()], 2)
        stress_50 = round(stress[np.abs(strain - 0.50).argmin()], 2)
        
        if dense_stress != "N/A":
            stress_dense = round(dense_stress, 2)
        else:
            stress_dense = "N/A"

        # Prepare data to display in tabulated form
        strain_data = [
            ["20 %", f"{stress_20} MPa"],
            ["50 %", f"{stress_50} MPa"],
            [f"Densification", f"{stress_dense} MPa"]
        ]

        headers = ["Strain (%)", "Stress"]

        print("\nKey Strain Values:")
        print(tabulate(strain_data, headers, tablefmt="grid"))

    def plot_control_limits(self, ax, ucl, lcl, strain):
        ax.plot(strain, ucl, color = 'r', label="UCL", linestyle='--',linewidth =0.6)
        ax.plot(strain, lcl, color = 'r', label="LCL", linestyle='--',linewidth =0.6)

    def plot_average_hysteresis(self, ax, testing = False) -> None:
        internal_plot = self.widget_manager.internal_plot_enabled.get()
        external_plot = self.widget_manager.external_plot_enabled.get()
        offset_value = float(self.widget_manager.offset_value)*100 if self.app.widget_manager.offset_value else 1 

         # Modulus line
        x,y  = self.app.variables.hyst_avg_linear_plot if self.app.variables.hyst_avg_linear_plot_best_fit is None else self.app.variables.hyst_avg_linear_plot_best_fit
        x_filtered, y_filtered, mask = self._filter_xy(x, y)
        print("\nAverage Plot: Slope of the modulus line: ", (y_filtered[-1] - y_filtered[0]) / (x_filtered[-1] - x_filtered[0]))
        ax.plot(x_filtered,y_filtered, color =  'g', label=f"{offset_value}% Modulus offset line", linestyle='--',linewidth =0.6) 

        # Plot strength points
        ps_strain, ps_stress = self.app.variables.avg_compressive_proof_strength_from_hyst[0] if self.app.variables.hyst_avg_linear_plot_best_fit is None else self.app.variables.avg_compressive_proof_strength_from_hyst[3]
        if  ps_strain and ps_stress:
                ax.scatter(ps_strain, ps_stress, color='g', label=f"Compressive Proof Strength ({ps_stress:.3f} MPa)")

        if internal_plot and not external_plot:
            self._plot_hysteresis_curve(ax)
        elif not internal_plot and external_plot:
            # plot only the modulus line
            pass
        else: # default plot everything
            self._plot_hysteresis_curve(ax)

            if testing == True:
                colours = ['r', 'y', 'm', 'c', 'k']
            
                for c, (ps_strain, ps_stress) in zip( colours, self.app.variables.avg_compressive_proof_strength_from_hyst[1:]):
                
                    if  ps_strain and ps_stress:
                        ax.scatter(ps_strain, ps_stress, color=c, label=f"Compressive Proof Strength ({ps_stress:.3f} MPa)")
                
                if self.app.variables.hyst_avg_linear_plot_by_mod: 
                    for c, plot in  zip( colours,[self.app.variables.hyst_avg_linear_plot_by_mod, self.app.variables.hyst_avg_linear_plot_secant, self.app.variables.hyst_avg_linear_plot_best_fit]):
                        x,y = plot
                        y_filtered = y[mask]
                        x_filtered = x[mask]
                        ax.plot(x_filtered,y_filtered, color=c, label=" 1% Modulus offset line", linestyle='--',linewidth =0.6)

                if self.app.variables.hyst_avg_linear_plot_filtered:
                    for key in self.app.variables.average_of_specimens_hysteresis_sm:
                        x,y = self.app.variables.hyst_avg_linear_plot_filtered[f'plot pts of {key}']
                        y_filtered = y[mask]
                        x_filtered = x[mask]

                        ax.plot(x_filtered,y_filtered, label=f" 1% with {key} and filter", linestyle='--',linewidth =0.6)

    def _filter_xy(self, x, y):
        max_stress = max(self.average_of_specimens["Stress"].to_numpy())
        mask_1 = x > 0
        mask_2 = y < max_stress
        mask = mask_1 & mask_2
        return x[mask], y[mask], mask
    
    def _plot_hysteresis_curve(self, ax) -> None:
        ax.plot(
            self.average_of_specimens_hysteresis["Strain"].to_numpy(),
            self.average_of_specimens_hysteresis["Stress"].to_numpy(),
            color='tab:purple',
            label="Average Hysteresis Curve",
            alpha=0.5
        )




     
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
     