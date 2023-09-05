# app/data_layer/IO/specimenIO.py

import glob
import json
import os
import string
import tempfile
import zipfile
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pydantic import parse_raw_as

if TYPE_CHECKING:
    from ..models import SpecimenDTO

class Idataformatter(ABC):
    @abstractmethod
    def read_and_clean_data() -> pd.DataFrame:
        pass

    @abstractmethod
    def deserialize() -> 'SpecimenDTO':
        pass

    @abstractmethod
    def serialize() -> str:
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

    def deserialize(self, zip_file_path: str) -> SpecimenDTO:
        """
        Deserialize a zip file back to a SpecimenDTO.

        Args:
        zip_file_path (str): Path to the serialized SpecimenDTO zip file.

        Returns:
        SpecimenDTO: The reconstructed SpecimenDTO object.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the zip to a temp directory
            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Load DTO from JSON
            with open(os.path.join(temp_dir, 'specimen_dto.json'), 'r') as json_file:
                dto_json = json_file.read()
                specimen_dto = parse_raw_as(SpecimenDTO, dto_json)

            # Load data content based on the file extension present returns a dataframe
            if os.path.exists(os.path.join(temp_dir, 'data_content.h5')):
                specimen_dto.data_content = pd.read_hdf(os.path.join(temp_dir, 'data_content.h5')) 
            elif os.path.exists(os.path.join(temp_dir, 'data_content.csv')):
                specimen_dto.data_content = pd.read_csv(os.path.join(temp_dir, 'data_content.csv'))
        
        return specimen_dto
    
    # export processed data

    def serialize(self, specimen_dto: SpecimenDTO, output_directory: str, data_format: str = 'hdf5') -> str:
            """
            Serialize the SpecimenDTO to a zip file.

            Args:
            specimen_dto (SpecimenDTO): The DTO to serialize.
            output_dir (str): Directory to save the serialized zip.
            data_format (str): Either 'hdf5' or 'csv' to decide the format of saving data content.
            """
            with tempfile.TemporaryDirectory() as temp_dir:
                # Serialize DTO to JSON
                dto_json = specimen_dto.json()

                # Save the data content based on chosen format
                data_file_path = None
                if specimen_dto.data_content is not None:
                    if data_format == 'hdf5':
                        data_file_path = os.path.join(temp_dir, 'data_content.h5')
                        specimen_dto.data_content.to_hdf(data_file_path, 'data')
                    elif data_format == 'csv':
                        data_file_path = os.path.join(temp_dir, 'data_content.csv')
                        specimen_dto.data_content.to_csv(data_file_path)
                    else:
                        raise ValueError("Unsupported format. Please choose either 'hdf5' or 'csv'.")

                # Define the zip file name based on some naming convention
                # Here, we'll just use the specimen name and a timestamp, but you can adjust as needed
                from datetime import datetime

                formatted_name = specimen_dto.name.replace(" ", "_") + "_" + datetime.now().strftime('%Y%m%d%H%M%S') + ".zip"

                valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
                filename = ''.join(c for c in formatted_name if c in valid_chars)

                zip_file_path = os.path.join(output_directory, formatted_name)

                # Add JSON and Data file (if present) to ZIP
                with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                    # Use the writestr method to write the JSON string to the ZIP
                    zipf.writestr('specimen_dto.json', dto_json)

                    # If data file exists, add it to the ZIP
                    if data_file_path:
                        zipf.write(data_file_path, os.path.basename(data_file_path))

            return zip_file_path  # return the path to the created zip for reference

   
    
