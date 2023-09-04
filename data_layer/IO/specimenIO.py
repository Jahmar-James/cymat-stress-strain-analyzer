# app/data_layer/IO/specimenIO.py

import pandas as pd
import glob
import json
import os
import zipfile
import tempfile
import string

import numpy as np

from abc import ABC, abstractmethod

class Idataformatter(ABC):
    @abstractmethod
    def read_and_clean_data() -> pd.DataFrame:
        pass
    
class SpecimenIO(Idataformatter):
    """
    Import Raw Data: Read and clean data from a specimen file
    Import Processed Data: Read custom zip file and load data into a specimen object
    Export Processed Data: Save specimen object to a custom zip file
    """
    TIME_ROW_IDENTIFIER = 'Data Acquisition'
    VALID_HEADERS = ['Displacement', 'Force', 'Time']

    def __init__(self):
        pass
    
    # import raw data
    def read_and_clean_data(self, file_path: str) -> pd.DataFrame:
        raw_data = self._read_raw_data(file_path)
        return self._clean_raw_data(raw_data)

    def _read_raw_data(self, file_path: str):
        with open(file_path, 'r') as file:
            return file.readlines()

    def _clean_raw_data(self, raw_data: list) -> pd.DataFrame:
        time_row_index = self._find_row_index_by_identifier(raw_data, self.TIME_ROW_IDENTIFIER)
        headers = self._extract_headers(raw_data, time_row_index)
        data_rows = self._extract_data_rows(raw_data, time_row_index, headers)
        return pd.DataFrame(data_rows, columns=headers)

    def _find_row_index_by_identifier(self, data: list, identifier: str) -> int:
        return next((index for index, line in enumerate(data) if line.startswith(identifier)), None)

    def _extract_headers(self, data: list, time_row_index: int) -> list:
        headers_row = data[time_row_index + 1].split()
        return [header for header in headers_row if header in self.VALID_HEADERS]

    def _extract_data_rows(self, data: list, time_row_index: int, headers: list) -> list:
        data_start_index = time_row_index + 3
        data_rows = []
        
        for line in data[data_start_index:]:
            if line.startswith(self.TIME_ROW_IDENTIFIER):
                continue
            if line.strip():
                data_rows.append(line.split()[:len(headers)])
                
        return data_rows
    
    # import processed data
    
    # Archived Implementation till specimen is refactored
    def load_specimen_data(self, file_path):
        from ..models import Specimen
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
 
        return specimen
     
    # export processed data
    
     # Archived Implementation till specimen is refactored
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
            specimen_file_name =  self._format_specimen_name_for_file(specimen.name)
            zip_file_path = os.path.join(output_directory, f'{specimen_file_name}_analyzer_data.zip')
            with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                for file in glob.glob(os.path.join(temp_dir, '*')):
                    zip_file.write(file, os.path.basename(file))
                    
    def _format_specimen_name_for_file(self, specimen_name):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in specimen_name if c in valid_chars)
        specimen_filename  = filename.replace(' ', '_')  # replace spaces with underscore
        if len(filename) > 50:  # check if filename is too long
            specimen_filename = filename[:50]
        return specimen_filename 

 

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
        from ..models import SpecimenDataManager, SpecimenGraphManager
        """
        Overrides the default method of json.JSONEncoder.

        Args:
        obj (object): The object to convert to JSON.

        Returns:
        dict or list or str or int or float or bool or None: The JSON-serializable representation of obj.
        """
        if isinstance(obj, 'SpecimenDataManager') or isinstance(obj, 'SpecimenGraphManager'):
            return self.encode_dict(obj.__dict__)
        else:
            return super().default(obj)

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
            elif isinstance(value, np.int64) or isinstance(value, pd.Int64Dtype):
                encoded_dict[attr] = int(value)  # Convert np.int64 to int
            elif isinstance(value, (pd.DataFrame,pd.Series, np.ndarray)):
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
