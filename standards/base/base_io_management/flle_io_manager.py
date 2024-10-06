import json
import tempfile
import zipfile
from pathlib import Path
from typing import Union

import pandas as pd

from standards.base.base_io_management.serializer import IOStrategy


class FileIOManager("IOStrategy"):
    # Main Methods Export and Import
    def export(self, tracked_object, registry: dict, output_dir: Path, database_uri) -> bool:
        if registry is None and output_dir is None:
            raise ValueError(
                "Registry and output_dir cannot be None. For exporting to a file, you must provide a registry and output directory."
            )
        return FileIOManager.export_to_file(registry, output_dir)

    def import_obj(self, return_class: object, input_file: Union[str, Path], **kwargs) -> object:
        file = input_file or [value for key, value in kwargs.items() if "file" in key.lower()][0]
        if isinstance(file, str):
            file = Path(input_file)

        if not isinstance(file, Path) or not file.exists():
            raise FileNotFoundError(f"File '{file}' does not exist or is not a valid Path object.")

        # Check if it's a zip file
        if file.is_file() and file.suffix == ".zip":
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                self._unzip_file(file, temp_dir_path)

                # Unzip if necessary
                if file.suffix == ".zip":
                    self._unzip_file(file, temp_dir_path)
                    json_file = temp_dir_path / "attributes.json"
                elif file.is_dir():
                    json_file = file / "attributes.json"
                else:
                    raise ValueError(f"Input '{file}' should either be a zip file or directory.")

                # Load attributes and data from the extracted files
                attributes = self._import_fields(temp_dir_path, json_file)

                # Instantiate and return the object using core attributes and data
                return IOStrategy.filter_and_instantiate(return_class, attributes, {})
        else:
            raise ValueError(f"Input '{file}' is not a valid zip file.")

    # Export Helpers Methods

    @staticmethod
    def export_to_file(registry: dict, output_dir: Path) -> bool:
        """
        Exports registered fields to JSON and CSV files, and then compresses them into a zip file.
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Export attributes to JSON
                json_file_path = FileIOManager._export_attributes_to_json(temp_path, registry["attributes"])

                # Export data to CSV
                csv_export_success = FileIOManager._export_data_to_csv(temp_path, registry["data"])

                # Zip the exported files
                zip_file_path = FileIOManager._zip_folder(temp_path, output_dir)

                # Check if the zip file exists
                return bool(zip_file_path.exists())

        except Exception as e:
            print(f"Error during file export: {e}")
            return False

    @staticmethod
    def _export_attributes_to_json(temp_path: Path, attributes: dict) -> Path:
        """
        Exports registered attributes to a JSON file.
        """
        # Invert dict key to have the output_name as the key and store the attribute_name as class_name
        formatted_attributes = {}

        for class_name, class_attribute in attributes.items():
            output_key = class_attribute.get("output_name", class_name)  # Default to class_name if no output_name
            formatted_attributes[output_key] = {"value": class_attribute["value"], "class_name": class_name}

        # Save the formatted attributes to a JSON file
        json_file_path = temp_path / "attributes.json"
        try:
            with open(json_file_path, "w") as file:
                json.dump(attributes, file, indent=4)
            return json_file_path
        except Exception as e:
            raise OSError(f"Failed to export attributes to JSON: {e}")

    @staticmethod
    def _export_data_to_csv(temp_path: Path, data: dict) -> bool:
        """
        Exports registered data to CSV files.
        """
        try:
            for attribute_name, details in data.items():
                value = details["value"]
                file_name = temp_path / f"{attribute_name}_data.csv"
                column_name = details.get("output_name", attribute_name)

                if isinstance(value, pd.Series):
                    value.name = column_name
                    value.to_csv(file_name, header=True, index=False)
                elif isinstance(value, pd.DataFrame):
                    # Handle DataFrame column renaming if output_name is a list of column names
                    if isinstance(column_name, list) and all(isinstance(name, str) for name in column_name):
                        value = value.copy()
                        value.rename(columns=dict(zip(value.columns, column_name)), inplace=True)
                    value.to_csv(file_name, header=True, index=True)
                else:
                    raise ValueError(f"Unsupported data type for CSV export: {type(value).__name__}")

            return True
        except Exception as e:
            print(f"Error exporting data to CSV: {e}")
            return False

    @staticmethod
    def _zip_folder(temp_path: Path, output_dir: Path) -> Path:
        """
        Create a zip file from the contents of a folder and return the zip file path.
        """
        zip_file_path = output_dir / f"{temp_path.name}.zip"
        try:
            with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)  # Relative path within the zip
                        zipf.write(file_path, arcname)
            return zip_file_path
        except Exception as e:
            raise OSError(f"Failed to zip folder: {e}")

    # Import Helpers Methods

    @staticmethod
    def _unzip_file(zip_file_path: Path, output_dir: Path) -> None:
        """
        Unzips the given zip file into the specified output directory.
        """
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(output_dir)
        except Exception as e:
            raise OSError(f"Failed to unzip file {zip_file_path}: {e}")

    @staticmethod
    def _import_fields(directory: Path, json_file: Path) -> dict:
        """
        Reads both attributes (from JSON) and data (from CSV) based on the registry in the JSON file.

        Returns:
        - A dictionary with correctly typed attributes and data.
        """
        try:
            # Load attributes and data from the JSON file
            with open(json_file, "r") as file:
                attributes = json.load(file)

            # Loop through attributes and handle both regular attributes and data files
            for attribute_name, details in attributes.items():
                # Check if this attribute refers to a data file (CSV)
                if "value" in details and isinstance(details["value"], str) and details["value"].endswith("_data.csv"):
                    csv_file_path = directory / details["value"]
                    if csv_file_path.exists():
                        # Load the CSV and apply correct type
                        attributes[attribute_name] = pd.read_csv(csv_file_path)

                        # Reassign the correct type for the data (usually Series or DataFrame)
                        attributes[attribute_name] = FileIOManager._reassign_type(
                            attributes[attribute_name], details["data_type"], attribute_name
                        )
                else:
                    # For non-data fields, reassign types if necessary
                    if "value" in details and "data_type" in details:
                        attributes[attribute_name]["value"] = FileIOManager._reassign_type(
                            details["value"], details["data_type"], attribute_name
                        )

            return attributes

        except Exception as e:
            raise OSError(f"Failed to load fields from {json_file}: {e}")

    @staticmethod
    def _reassign_type(value, data_type: str, attribute_name: str):
        """
        Reassigns the correct type to an attribute or data field based on its original class.

        Parameters:
        - value: The value to reassign a type to.
        - data_type: The string name of the original data type.
        - attribute_name: The name of the attribute for context in error handling.

        Returns:
        - The value with the correct type reassigned.
        """
        try:
            if hasattr(__builtins__, data_type):
                return getattr(__builtins__, data_type)(value)
            elif hasattr(pd, data_type):
                # If it's a pandas type (e.g., Series or DataFrame)
                if data_type == "Series":
                    return pd.Series(value)
                elif data_type == "DataFrame":
                    return pd.DataFrame(value)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            raise ValueError(f"Failed to reassign type for attribute '{attribute_name}': {e}")
