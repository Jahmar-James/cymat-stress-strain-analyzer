import glob
import json
import os
import string
import tempfile
import threading
import zipfile
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import numpy as np
import pandas as pd

from excel_exporter import ExcelExporter
from ms_word_exporter import WordExporter
from specimen import Specimen

DIN_PROPERTIES = [
        'Rplt', 'Rplt_E', 'ReH', 'Ev', 'Eff', 'ReH_Rplt_ratio', 'Aplt_E', 'AeH', 'Rp1', 'm'
    ]

def is_float(value: str) -> bool:
    return value.replace('.', '', 1).isdigit()

# data_handler.py
class DataHandler:
    """
    Handles data manipulation and management tasks for the application. 

    Attributes:
    app (object): The main application object.
    excel_exporter (ExcelExporter): An ExcelExporter instance for exporting data to Excel.
    widget_manager (WidgetManager): Manages the GUI widgets of the application.
    button_actions (dict): Maps button names to their corresponding actions.
    properties_df (DataFame): df containing key properties for all selected speicmen 
    """
    def __init__(self, app):
        self.app = app
        self.excel_exporter = ExcelExporter(self.app)
        self.word_exporter = WordExporter(self.app)
        self.general_properties = ['name', 'length', 'width', 'thickness', 'weight', 'density', 'youngs_modulus']
        self.data_manager_properties = ['toughness','ductility','resilience']
        self.din_properties = DIN_PROPERTIES
        self.properties_df =  pd.DataFrame()
        self.data_analysis_buttons = []  # First group
        self.data_management_buttons = []  # Second group
    
    def set_widget_manager(self, widget_manager):
        self.widget_manager = widget_manager

    def set_button_actions(self, button_actions):
        self.button_actions = button_actions

    @property
    def average_of_specimens(self):
        return self.app.variables.average_of_specimens
    
    def validate_and_import_data(self) -> Optional[str]:
        name, length, width, thickness, weight = self.get_specimen_properties()

        if not all([name, length, width, thickness, weight]):
            return "All fields must be filled."

        if not all([is_float(value) for value in [length, width, thickness, weight]]):
            return "Length, Width, Thickness, and Weight must be numbers."
        return None

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
            self.app.variables.selected_indices = selected_indices
        
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
          
    def calculate_summary_stats(self, values):
        average_value = np.mean(values)
        std_value = np.std(values)
        cv_value = (std_value / average_value) * 100 if average_value != 0 else 0
        return average_value, std_value, cv_value

    def summary_statistics(self):
        """Calculate summary statistics for each property."""
        summary_df = self.create_summary_df(self.properties_df)
        return summary_df
  
    def create_properties_df(self, selected_specimens = None):
        """Create a DataFrame with all properties for each specimen."""
        selected_specimens = self.get_selected_specimens() if selected_specimens is None else selected_specimens

        properties_dfs = []

        for specimen in selected_specimens:
            specimen_properties = self.get_specimen_full_properties(specimen)
            specimen_df = pd.DataFrame(specimen_properties, index=[specimen.name])
            properties_dfs.append(specimen_df)
        
        properties_df = pd.concat(properties_dfs)

        return properties_df
    
    def get_specimen_full_properties(self, specimen):
        """Extracts the properties of a specimen."""
        properties = {}

        # Get general properties
        for prop in self.general_properties:
            properties[prop] = getattr(specimen, prop)
        
        # Get DIN analysis properties
        for prop in self.din_properties:
            try:
                properties[prop] = getattr(specimen.din_analyzer, prop)
            except AttributeError:
                print(f'Error: din_analyzer not initialized for specimen: {specimen}')
            
        # Get data manager properties
        for prop in self.data_manager_properties:
            properties[prop] = getattr(specimen.data_manager, prop)
        
        return properties

    def create_summary_df(self, properties_df):
        """Create a summarized DataFrame of their average with the corresponding STD and CV."""
        summary_stats = []

        for prop in properties_df.columns:
            if prop != 'name':  # skip over 'name' column
                avg, std, cv = self.calculate_summary_stats(properties_df[prop].values)
                summary_stats.append({'Property': prop, 'Average': avg, 'Std Dev': std, 'CV %': cv})
     
        summary_stats_df = pd.DataFrame(summary_stats)
        summary_stats_df.set_index('Property', inplace=True)

        return summary_stats_df
    
    def update_properties_df(self, selected_indices):
        selected_specimens = self.get_selected_specimens(selected_indices)
        for specimen in selected_specimens:
            if specimen.din_analyzer is None:
                specimen.set_analyzer()

        # Update specimen properties DataFrame
        self.properties_df = self.create_properties_df(selected_specimens)

    def export_average_to_excel(self,selected_indices, file_path):
    
        self.update_properties_df(selected_indices)

        print("Starting export thread")
        export_thread = threading.Thread(target=self.excel_exporter.export_data_to_excel(selected_indices, file_path))
        # export_thread = threading.Thread(target=self.excel_exporter.profile_export_average_to_excel)
        export_thread.start()
        self.app.variables.export_in_progress = True

    def format_specimen_name_for_file(self, specimen_name):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in specimen_name if c in valid_chars)
        specimen_filename  = filename.replace(' ', '_')  # replace spaces with underscore
        if len(filename) > 50:  # check if filename is too long
            specimen_filename = filename[:50]
        return specimen_filename 
    
    def export_DIN_to_word(self,selected_indices, file_path):
        self.update_properties_df(selected_indices)

        print("Starting export thread")
        export_thread = threading.Thread(target=self.word_exporter.export_report(selected_indices, file_path))
          

    def save_specimen_data(self, specimen, output_directory):
        """
        Saves the specimen data to a temporary directory and then zips the files.

        Args:
        specimen (Specimen): The specimen to save.
        output_directory (str): The directory where to save the zipped file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Serialize specimen properties to JSON
            properties_dict = specimen.__dict__
            with open(os.path.join(temp_dir, 'specimen_properties.json'), 'w') as json_file:
                json.dump(properties_dict, json_file, cls=SpecimenDataEncoder, export_dir=temp_dir)

            # Zip all generated files
            specimen_file_name =  self.format_specimen_name_for_file(specimen.name)
            zip_file_path = os.path.join(output_directory, f'{specimen_file_name}_analyzer_data.zip')
            with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                for file in glob.glob(os.path.join(temp_dir, '*')):
                    zip_file.write(file, os.path.basename(file))

    def load_specimen_data(self, file_path):
        """
        Loads the specimen data from a zipped file.

        Args:
        file_path (str): The path to the zipped file containing the specimen data.
        """
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
    """
    Custom JSONEncoder subclass that knows how to encode custom specimen data types.

    Attributes:
    export_dir (str): Directory where data files are exported.
    """
    def __init__(self, *args, **kwargs):
        # accept the export directory as an argument
        self.export_dir = kwargs.pop("export_dir", ".")
        super().__init__(*args, **kwargs)

    def default(self, obj):
        """
        Overrides the default method of json.JSONEncoder.

        Args:
        obj (object): The object to convert to JSON.

        Returns:
        dict or list or str or int or float or bool or None: The JSON-serializable representation of obj.
        """
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
        """
        Encodes a dictionary into a JSON-friendly format.

        Args:
        obj_dict (dict): The dictionary to encode.

        Returns:
        dict: The encoded dictionary.
        """
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
