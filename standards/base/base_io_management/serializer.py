from collections import namedtuple
from typing import Optional, Union

import pandas as pd
from pathlib import Path

import tempfile
import json
import zipfile

AttributeField = namedtuple('AttributeField', ['attribute_name', 'value', 'unit', 'output_name', 'category'])

class Serializer:
    def __init__(self, tracked_object = None):
        self._registry = {
            'attributes': {},  # For storing attributes to be serialized into JSON
            'data': {}         # For storing data to be serialized into CSV
        }
        self.tracked_object = tracked_object
          
    def register_list(self, data: list[AttributeField]) -> bool:
        """Register a list of fields for serialization/export."""
        return all(self.register_field(item) for item in data)
        
    def register_field(self, field:Union[AttributeField, tuple], tracked_object: Optional[object]= None) -> bool:
        """
        Register a single field, ensuring that the attribute exists on the tracked object.
        """
        if tracked_object:
            self.tracked_object = tracked_object
        
        if self.tracked_object is None:
            raise ValueError(
                "Cannot register field because the tracked object is not set. "
                "Make sure to pass a valid object to the Serializer."
                )   
        
        if not isinstance(field, AttributeField) and len(field) == 5:
            field = AttributeField(*field)
        else:
            raise TypeError(
                    f"Expected 'AttributeField' or tuple of length 5, but got {type(field).__name__} with length {len(field)}. "
                    "Make sure you're passing a namedtuple 'AttributeField' or a valid tuple."
                )
        
        if not hasattr(self.tracked_object, field.attribute_name):
            raise AttributeError(
                f"'{self.tracked_object.__class__.__name__}' object has no attribute '{field.attribute_name}'. "
                "Ensure the attribute exists on the object being tracked. You passed an invalid field: "
                f"'{field.attribute_name}' is not present on '{self.tracked_object.__class__.__name__}'."
            )
        
        output_name = field.output_name or self._generate_output_name(field.attribute_name, field.unit)

        # Store the field in the correct category in the registry
        self._registry[field.category][field.attribute_name] = {
            'value': field.value,
            'unit': field.unit,
            'output_name': output_name,  
        }
        return True
        
    @staticmethod
    def _generate_output_name(name: str, unit: Optional[str]) -> str:
        """Generate a standardized output name, appending unit if provided."""
        return f'{name} ({unit})' if unit else name
    
    def export_to_file(self, output_dir: Path) -> bool:
        """Export registered fields to JSON and CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Export attributes to JSON
            self._export_attributes_to_json(temp_path / 'attributes.json')
            
            # Export data to CSV
            self._export_data_to_csv(temp_path)
            
            # Zip the exported files
            zip_file_path = self._zip_folder(temp_path, output_dir)
            return bool(zip_file_path.exists())

    
    def _export_attributes_to_json(self, file_name: Optional[Path] = None):
        """Export registered attributes to a JSON file."""
        attributes_dict = self._extract_registered_data('attributes')
        if file_name is None:
            file_name = Path.cwd() / 'attributes.json'
        with open(file_name, 'w') as file:
            json.dump(attributes_dict, file, indent=4)
            
    def _export_data_to_csv(self, output_dir: Path):
        """Export registered data to a CSV file."""
        for attribute_name, details in self._registry['data'].items():
            value = details['value']
            file_name = output_dir / f"{attribute_name}_data.csv"
            column_name = details['output_name'] or attribute_name 
            
            if isinstance(value, pd.Series):
                value.name = column_name
                value.to_csv(file_name, header=True, index=False)
            elif isinstance(value, pd.DataFrame):
                if isinstance(column_name, list) and all(isinstance(name, str) for name in column_name):
                    value = value.copy()
                    value.rename(columns=dict(zip(value.columns, column_name)), inplace=True)
                    value.to_csv(file_name, header=True, index=True)
                value.to_csv(file_name, header=True, index=True)
            else:
                raise ValueError(
                    f"Unsupported data type for CSV export: {type(value).__name__}. "
                    "Expected 'pandas.Series' or 'pandas.DataFrame'. Please ensure the data is in one of these formats."
                )
            
    def _extract_registered_data( self, category: str,) -> dict[str, Union[str, int, float]]:
        """Extracts the registered data from the registry for a given category."""
        if category not in ['attributes', 'data']:
            raise ValueError(
                f"Invalid category '{category}'. Allowed categories are 'attributes' and 'data'. "
                "Check that you are using the correct category."
            )
        output_dict = {}
        for name, details in self._registry[category].items():
            output_key = details['output_name']
            output_dict = {
                output_key: details['value'],
                'sammple_property': name,
            }

        return output_dict
    
    @staticmethod
    def _zip_folder(folder_path: Path, output_dir: Path) -> Path:
        """Create a zip file from the contents of a folder and return the zip file path."""
        zip_file_path = output_dir / f"{folder_path.name}.zip"
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():  # Only add files to the zip, not directories
                    arcname = file_path.relative_to(folder_path)  # Relative path within the zip
                    zipf.write(file_path, arcname)
        return zip_file_path
         