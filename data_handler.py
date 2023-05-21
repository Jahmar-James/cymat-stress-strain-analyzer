import glob
import json
import os
import tempfile
import threading
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import numpy as np
import pandas as pd

from excel_exporter import ExcelExporter
from specimen import Specimen


def is_float(value: str) -> bool:
    return value.replace('.', '', 1).isdigit()

# data_handler.py
class DataHandler:
    def __init__(self, app):
        self.app = app
        self.excel_exporter = ExcelExporter(self.app)
    
    def set_widget_manager(self, widget_manager):
        self.widget_manager = widget_manager

    def set_button_actions(self, button_actions):
        self.button_actions = button_actions

    @property
    def average_of_specimens(self):
        return self.app.variables.average_of_specimens

    def import_specimen_data(self):
        def read_raw_data(file_path):
            with open(file_path, 'r') as file:
                return file.readlines()
        
        def clear_entries():
            self.button_actions.clear_entries()

        DAT_FILE_TYPE = (("Data files", "*.dat"), ("All files", "*.*"))
        
        file_path = filedialog.askopenfilename(title="Select a data file",
                                            filetypes=(DAT_FILE_TYPE))
        if file_path:
            # Display file name above the 'Import Data' button
            filename = Path(file_path).name
            raw_data = read_raw_data(file_path)
            name, length, width, thickness, weight = self.get_specimen_properties()

            specimen = Specimen(name, raw_data, length, width, thickness, weight)
            specimen.calculate_properties()
            
            self.widget_manager.update_ui_elements(filename, specimen)
            
            specimen.process_data()
            tab_id = self.widget_manager.create_new_tab(name)
            self.app.variables.add_specimen(tab_id, specimen)

            clear_entries()
            # Run specimen.find_IYS_align() in a separate thread
            find_IYS_align_thread = threading.Thread(target=specimen.find_IYS_align)

            # Start the new thread
            find_IYS_align_thread.start()
            
             # Wait for the find_IYS_align_thread to finish
            find_IYS_align_thread.join()
            if len(self.app.variables.specimens) > 1:
                self.button_actions.plot_all_specimens()
        

    def get_specimen_properties(self):
        name = self.widget_manager.name_entry.get()
        length = self.widget_manager.length_entry.get()
        width = self.widget_manager.width_entry.get()
        thickness = self.widget_manager.thickness_entry.get()
        weight = self.widget_manager.weight_entry.get()
        return name, length, width, thickness, weight
    
    def validate_and_import_data(self) -> Optional[str]:
        name, length, width, thickness, weight = self.get_specimen_properties()

        if not all([name, length, width, thickness, weight]):
            return "All fields must be filled."

        if not all([is_float(value) for value in [length, width, thickness, weight]]):
            return "Length, Width, Thickness, and Weight must be numbers."
        return None

    def get_common_strain(self, selected_specimens):
        max_strain = max(specimen.shifted_strain.max() for specimen in selected_specimens)
        max_num_points = max(len(specimen.shifted_strain) for specimen in selected_specimens)
        common_strain = np.linspace(0, max_strain, num=max_num_points)
        return common_strain

    def get_interpolated_stresses(self, selected_specimens, common_strain):
        interpolated_stresses = [np.interp(common_strain, specimen.shifted_strain, specimen.stress) for specimen in selected_specimens]
        return interpolated_stresses
    
    def get_common_displacement(self, selected_specimens):
        max_displacement = max(specimen.shifted_displacement.max() for specimen in selected_specimens)
        max_num_points = max(len(specimen.shifted_displacement) for specimen in selected_specimens)
        common_displacement = np.linspace(0, max_displacement, num=max_num_points)
        return common_displacement

    def get_interpolated_forces(self, selected_specimens, common_displacement):
        interpolated_forces = [np.interp(common_displacement, specimen.shifted_displacement, specimen.force) for specimen in selected_specimens]
        return interpolated_forces
    
    def get_selected_specimens(self, selected_indices=None):
        if selected_indices is None:
            selected_indices = self.widget_manager.specimen_listbox.curselection()
            self.app.variables.selected_indices =selected_indices
        
        selected_specimens = [self.app.variables.specimens[index] for index in selected_indices]
        return selected_specimens

    def average_of_selected_specimens(self, selected_indices=None):
        selected_specimens = self.get_selected_specimens(selected_indices)
        if not selected_specimens:
            return
        
        self.app.variables.selected_specimen_names = [specimen.name for specimen in selected_specimens]

        common_displacement = self.get_common_displacement(selected_specimens)
        interpolated_forces = self.get_interpolated_forces(selected_specimens, common_displacement)

        average_force = np.mean(interpolated_forces, axis=0)
        average_displacement = common_displacement

        common_strain = self.get_common_strain(selected_specimens)
        interpolated_stresses = self.get_interpolated_stresses(selected_specimens, common_strain)

        average_stress = np.mean(interpolated_stresses, axis=0)
        average_strain = common_strain

        self.app.variables.average_of_specimens = pd.DataFrame({
        "displacement": average_displacement,
        "force": average_force,
        "strain": average_strain,
        "stress": average_stress
    })
    
    def export_data(self):
        for specimen in self.app.variables.specimens:
            specimen.data_manager.export_to_excel(f"{specimen.name} cleaned data.xlsx")
        tk.messagebox.showinfo("Data Export", "Data has been exported to Excel successfully!")

    def export_average_to_excel(self):
        print("Starting export thread")
        export_thread = threading.Thread(target=self.excel_exporter.export_average_to_excel)
        # export_thread = threading.Thread(target=self.excel_exporter.profile_export_average_to_excel)
        export_thread.start()

    def save_specimen_data(self, specimen, output_directory):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Serialize specimen properties to JSON
            properties_dict = specimen.__dict__
            with open(os.path.join(temp_dir, 'specimen_properties.json'), 'w') as json_file:
                json.dump(properties_dict, json_file, cls=SpecimenDataEncoder, export_dir=temp_dir)

            # Zip all generated files
            zip_file_path = os.path.join(output_directory, f'{specimen.name}_analyzer_data.zip')
            with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                for file in glob.glob(os.path.join(temp_dir, '*')):
                    zip_file.write(file, os.path.basename(file))

    def load_specimen_data(self, file_path):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Unzip the file
            with zipfile.ZipFile(file_path, 'r') as zipf:
                zipf.extractall(temp_dir)

            # Load properties from the JSON file
            with open(os.path.join(temp_dir, 'specimen_properties.json'), 'r') as fp:
                properties_dict = json.load(fp)

            # Reconstruct the Specimen object
            specimen = Specimen.from_dict(properties_dict, temp_dir=temp_dir)
            # Add to GUI
            tab_id = self.widget_manager.create_new_tab(specimen.name)
            self.app.variables.add_specimen(tab_id, specimen)
            self.widget_manager.enable_buttons()
            filename = Path(file_path).name
            self.widget_manager.update_ui_elements(filename, specimen)
        return 


class SpecimenDataEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        # accept the export directory as an argument
        self.export_dir = kwargs.pop("export_dir", ".")
        super().__init__(*args, **kwargs)

    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            if isinstance(obj, dict):
                return self.encode_dict(obj)
            elif hasattr(obj, '__dict__'):
                return self.encode_dict(obj.__dict__)
            else:
                raise

    def encode_dict(self, obj_dict):
        encoded_dict = {}
        for attr, value in obj_dict.items():
            if attr == "raw_data" or attr == "specimen":
                continue  # Skip raw_data and specimen
            elif isinstance(value, dict):
                encoded_dict[attr] = self.encode_dict(value)  # recursively handle nested dictionaries
            elif isinstance(value, np.int64):
                encoded_dict[attr] = int(value)  # Convert np.int64 to int
            elif isinstance(value, (pd.DataFrame, np.ndarray)):
                csv_filename = f'{attr}_data.csv'
                csv_filepath = os.path.join(self.export_dir, csv_filename)
                if isinstance(value, pd.DataFrame):
                    value.to_csv(csv_filepath, index=False)
                else:
                    np.savetxt(csv_filepath, value, delimiter=",")
                encoded_dict[attr] = os.path.basename(csv_filename)
            else:
                encoded_dict[attr] = value
        return encoded_dict


