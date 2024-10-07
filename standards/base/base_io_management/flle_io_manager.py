import json
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from standards.base.base_io_management.serializer import IOStrategy


class FileIOManager(IOStrategy):
    STRATEGY_NAME = "File_IO"
    # Main Methods Export and Import
    def export(self, tracked_object: object, registry: dict, **kwargs) -> bool:
        """
        Exports the registry of a tracked object to the specified output path.

        Assumptions:
        ------------
        - `tracked_object` contains sufficient data and metadata for serialization.
        - `registry` is a validated dictionary that holds the data to be exported.

        kwargs:
        - `output_path` is a valid `Path` object, either pointing to a file or a directory.
        - If `output_path` is a directory, the backend will generate a file name based on the `tracked_object`.

        Preconditions:
        --------------
        - `registry` must not be `None` and must be properly initialized with valid data.
        - `output_path` must not be `None`. It must either point to:
          - A valid file path, or
          - A valid directory where the backend can create a file (if no file name is provided).
        - The parent directory of `output_path` must already exist. The backend will not create directories.
        - `tracked_object` should provide attributes (e.g., `name`, `version`, `software_version`) required for generating a file name if `output_path` is a directory.

        Postconditions:
        ---------------
        - The data will be exported to the specified `output_path`, including the generated file name if only a directory is provided.
        - If the operation is successful, the function will return `True`.
        - If any precondition is violated, the function will raise an appropriate error:
          - `ValueError` for invalid inputs such as `None` values or missing data.
          - `OSError` if the directory does not exist or cannot be accessed.
        - The backend will not silently correct any errors; it will raise exceptions for the frontend to handle.

        Returns:
        --------
        - `True` if the export was successful.
        """
        # Validate registry keys and output path
        output_path = kwargs.get("output_path", None)
        if output_path is None:
            path = next((value for key, value in kwargs.items() if "path" in key.lower()), None)
            if path is None:
                raise ValueError(
                    f"Cannot export object without a valid output path. Please provide a valid output path to export the object '{tracked_object}'."
                )
            output_path = path if isinstance(path, Path) else Path(path)

        IOValidator.validate_registry_exists(registry, func_name="Export(FileIOManager)")
        IOValidator.validate_registry(registry, required_keys=["attributes", "data"], func_name="Export(FileIOManager)")
        IOValidator.validate_output_path(output_path, func_name="export to file")
        IOValidator.validate_output_extension(
            output_path, allowed_extensions=[".zip", ""], func_name="Export(FileIOManager)"
        )

        # If the output path is a directory, generate a file name and append it
        if output_path.is_dir():
            file_name = self.generate_file_name(tracked_object)
            output_path = output_path / file_name

        # Check if parent directory exists and fail fast if not
        if not output_path.parent.exists():
            raise IOValidator.generate_file_not_found_error(
                output_path.parent, suggestion="Please create the directory or provide a valid path."
            )

        return self.export_to_file(registry, output_path)

    def import_obj(self, id: Optional[int], name: Optional[str], return_class: object, **kwargs) -> object:
        """
        Imports an object from a zip file, extracting and loading its data.

        Preconditions:
        --------------
        - `return_class` is the class of the object to be imported.
        - The `kwargs` must contain a valid file path under the key 'file'.

        Postconditions:
        ---------------
        - A zip file is extracted, and the JSON and CSV data are loaded.
        """
        # Check if 'file' is passed in the kwargs

        input_file = kwargs.get("input_file", None)
        # If input_file is not provided, try to find a file key in kwargs
        if input_file is None:
            file = next((value for key, value in kwargs.items() if "file" in key.lower()), None)

            if not file:
                raise ValueError(
                    "Cannot import object without a valid file path. Please provide a valid file path to import the object."
                )

            input_file = file if isinstance(file, Path) else Path(file)

        # Call the specific method to import the object from the file
        return self.import_object_from_file(return_class, input_file)

    # Export Helpers Methods

    @staticmethod
    def export_to_file(registry: dict, output_path: Path) -> bool:
        """
        Exports registered fields to JSON and CSV files, and then compresses them into a zip file.

        Preconditions:
        --------------
        - `registry` contains at least two keys: 'attributes' and 'data'.
        - `output_path` is a valid path, including a file name with a .zip extension.
        - The parent directory of `output_path` exists.

        Postconditions:
        ---------------
        - A zip file is created at `output_path` containing the JSON and CSV files generated from the registry.
        - Returns True if the export and compression are successful, otherwise raises an appropriate error.
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Export attributes to JSON
                FileIOManager._export_attributes_to_json(temp_path, registry["attributes"])

                # Export data to CSV
                FileIOManager._export_data_to_csv(temp_path, registry["data"])

                # Zip the exported files
                zip_file_path = FileIOManager._zip_folder(temp_path, output_path)

                # Check if the zip file exists
                return bool(zip_file_path.exists())

        except FileNotFoundError as e:
            raise IOValidator.generate_file_not_found_error(
                output_path, suggestion="Ensure all file paths are correct."
            )
        except PermissionError as e:
            raise IOValidator.generate_permission_error(task="write to the file", path=output_path)
        except OSError as e:
            raise IOValidator.generate_os_error(task="export data", path=output_path)
        except Exception as e:
            raise Exception(f"An unexpected error occurred during file export: {e}")

    @staticmethod
    def _export_attributes_to_json(temp_path: Path, attributes: dict) -> Path:
        """
        Exports registered attributes to a JSON file.
        """
        # Invert dict key to have the output_name as the key and store the attribute_name as class_name
        formatted_attributes = {}

        for class_name, class_attribute in attributes.items():
            output_key = class_attribute.get("output_name", class_name)  # Default to class_name if no output_name
            formatted_attributes[output_key] = {
                "value": class_attribute["value"],
                "class_name": class_name,
                "data_type": class_attribute["data_type"],
                "unit": class_attribute.get("unit", None),
            }

        # Save the formatted attributes to a JSON file
        json_file_path = temp_path / "attributes.json"
        try:
            with open(json_file_path, "w") as file:
                json.dump(formatted_attributes, file, indent=4)
            return json_file_path
        except PermissionError as e:
            raise IOValidator.generate_permission_error(task="write JSON file", path=json_file_path)
        except OSError as e:
            raise IOValidator.generate_os_error(task="write JSON file", path=json_file_path)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while exporting attributes to JSON: {e}")

    @staticmethod
    def _export_data_to_csv(temp_path: Path, data: dict) -> bool:
        """
        Exports registered data to CSV files.
        """
        for attribute_name, details in data.items():
            value = details["value"]
            file_name = temp_path / f"{attribute_name}_data.csv"
            column_name = details.get("output_name", attribute_name)

            try:
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
                    raise IOValidator.generate_value_error(
                        value_type=type(value).__name__,
                        attribute_name=attribute_name,
                        expected_types="Series or DataFrame",
                    )

            except PermissionError as e:
                raise IOValidator.generate_permission_error(
                    task=f"write CSV file for '{attribute_name}'", path=file_name
                )
            except OSError as e:
                raise IOValidator.generate_os_error(task=f"write CSV file for '{attribute_name}'", path=file_name)
            except Exception as e:
                raise Exception(f"An unexpected error occurred while exporting '{attribute_name}' to CSV: {e}")

        # Check if all data files were successfully created
        return all((temp_path / f"{attribute_name}_data.csv").exists() for attribute_name in data)

    @staticmethod
    def _zip_folder(temp_path: Path, output_path: Path) -> Path:
        """
        Create a zip file from the contents of a folder and return the zip file path.

        Preconditions:
        --------------
        - `temp_path` contains the files to be zipped.
        - `output_path` is a valid path with a .zip file name.

        Postconditions:
        ---------------
        - A zip file is created at `output_path` containing all files in `temp_path`.
        - Returns the path to the created zip file.
        """

        zip_file_path = output_path if output_path.suffix == ".zip" else output_path.with_suffix(".zip")
        try:
            with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)  # Relative path within the zip
                        zipf.write(file_path, arcname)
            return zip_file_path
        except PermissionError as e:
            raise IOValidator.generate_permission_error(task="write ZIP file", path=zip_file_path)
        except OSError as e:
            raise IOValidator.generate_os_error(task="create ZIP file", path=zip_file_path)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while creating the ZIP file: {e}") @ staticmethod

    @staticmethod
    def generate_file_name(
        tracked_object,
        extension="zip",
        data_type: Optional[str] = "MTAnalyzerData",
        standard: Optional[str] = "general",
    ) -> str:
        """
        Generates a file name based on the object's properties.
        """
        # 1. Get the object's name or fallback to class name
        object_name = getattr(tracked_object, "name", tracked_object.__class__.__name__)

        # 2. Get the standard or fallback to 'general'
        standard = getattr(tracked_object, "standard", standard)

        # 3. Get the Version or fallback to 'v1'
        version = getattr(tracked_object, "version", "v1")
        # Custom version for Application Object
        if hasattr(tracked_object, "entity_version"):
            version = getattr(tracked_object, "entity_version", "v1")

        # 4. Get the data type or fallback to signature default
        data_type = getattr(tracked_object, "data_type", data_type)

        # 5. Export / Software Version
        software_version = getattr(tracked_object, "software_version", "sv1")

        # 6. Construct the file name with the object's properties
        file_name = f"{object_name}_{standard}_V{version}_{data_type}_SV{software_version}.{extension}"

        # Example: 'Sample1_general_v1_MTAnalyzerData_sv1.zip'
        return file_name

    # Import Helpers Methods
    @staticmethod
    def import_object_from_file(return_class: object, input_file: Union[str, Path]) -> object:
        """
        Imports an object from a zip file, extracting and loading its data.

        Preconditions:
        --------------
        - `input_file` must be a valid file path (either passed directly or through `kwargs`).
        - The input file must exist and be a valid `.zip` file.
        - The extracted file must contain an `attributes.json` file.

        Postconditions:
        ---------------
        - A zip file is extracted, and the JSON and CSV data are loaded.
        - An object of `return_class` is instantiated using the extracted attributes and data.
        - Returns the instantiated object or raises an appropriate error if the import fails.
        """

        # Convert to Path if input_file is a string
        file = Path(input_file) if isinstance(input_file, str) else input_file

        IOValidator.validate_file_exists(file, func_name="import_object_from_file")
        IOValidator.validate_output_extension(
            file, allowed_extensions=[".zip", ""], func_name="import_object_from_file"
        )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)

                # Unzip file and validate the presence of extracted attributes.json
                FileIOManager._unzip_file(file, temp_dir_path)  # Unzipping the file
                json_file = temp_dir_path / "attributes.json"
                IOValidator.validate_file_exists(
                    json_file, func_name="import_object_from_file"
                )  # Check extracted JSON once

                # Load attributes and data from the extracted files
                attributes_n_data = FileIOManager._load_attributes_and_data(temp_dir_path, json_file)

                # Instantiate and return the object using core attributes and data
                return IOStrategy.filter_and_instantiate(return_class, attributes_n_data, {})

        except Exception as e:
            raise Exception(f"Error occurred while importing object from '{file}': {e}")

    @staticmethod
    def _unzip_file(zip_file_path: Path, output_dir: Path) -> None:
        """
        Unzips the given zip file into the specified output directory.

        Preconditions:
        --------------
        - `zip_file_path` is a valid path to an existing zip file.
        - `output_dir` is a valid directory where the extracted files will be stored.

        Postconditions:
        ---------------
        - The contents of the zip file are extracted into `output_dir`.
        - Raises a PermissionError, OSError, or other relevant exception if the extraction fails.
        """
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(output_dir)
        except PermissionError as e:
            raise IOValidator.generate_permission_error(task="unzip file", path=output_dir)
        except OSError as e:
            raise IOValidator.generate_os_error(task="unzip file", path=zip_file_path)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while unzipping '{zip_file_path}': {e}")

    @staticmethod
    def _load_attributes_and_data(directory: Path, json_file: Path) -> dict:
        """ "
        Reads attributes from a JSON file and associated data from CSV files.

        Preconditions:
        --------------
        - `directory` is a valid directory containing the extracted files.
        - `json_file` is a valid path to an existing JSON file within the directory.

        Postconditions:
        ---------------
        - Attributes are loaded from the JSON file.
        - CSV data files referenced in the JSON are read and their types reassigned (Series, DataFrame).
        - Returns a dictionary of attributes with correctly reassigned data types.
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

        except OSError as e:
            raise IOValidator.generate_os_error(task="load fields from JSON", path=json_file)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while loading fields from '{json_file}': {e}")

    @staticmethod
    def _reassign_type(value, data_type: str, attribute_name: str):
        """
        Reassigns the correct type to an attribute or data field based on its original class.

        Preconditions:
        --------------
        - `value` is the value to reassign.
        - `data_type` is a string representing the original data type (Series, DataFrame, etc.).

        Postconditions:
        ---------------
        - Returns the value with the correct type reassigned (Series, DataFrame, etc.).
        - Raises a ValueError if the data type is unsupported or cannot be reassigned.
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
            if data_type.endswith("_enum"):
                return check_enums(value, data_type)
            else:
                raise IOValidator.generate_value_error(
                    value_type=data_type,
                    attribute_name=attribute_name,
                    expected_types="Series, DataFrame, or other supported types",
                )
        except Exception as e:
            raise ValueError(f"Failed to reassign type for attribute '{attribute_name}': {e}")


def check_enums(value, data_type: str):
    # Remove the '_enum' suffix to get the actual Enum class
    data_type = data_type.replace("_enum", "")

    # Import here to avoid circular imports for all enums
    from standards.base.analyzable_entity import DataState

    if data_type == "DataState":
        return DataState(value)
    else:
        return value


# IOValidator stays focused on validation and error formatting
class IOValidator:

    # General Export Strategy
    @staticmethod
    def validate_registry_exists(registry: dict, func_name: str = "") -> None:
        """Ensure the registry is not None."""
        if registry is None:
            raise ValueError(
                f"Error in {func_name}: Registry is None. Please ensure the registry is properly initialized."
            )

    @staticmethod
    def validate_registry(registry: dict, required_keys: list[str], func_name: str = "") -> None:
        """Ensure the registry contains all required keys."""
        missing_keys = [key for key in required_keys if key not in registry]
        if missing_keys:
            raise KeyError(f"{func_name}: Registry is missing required keys: {', '.join(missing_keys)}.")
        
     # File Export Strategy
     # Post Conditions Validation
    @staticmethod
    def validate_output_path(output_path: Path, func_name: str = "") -> None:
        """Ensure the output path is valid."""
        if output_path is None:
            raise ValueError(f"Error in {func_name}: Output path cannot be None. Please specify a valid output path to export.")
        
    @staticmethod
    def validate_file_exists(file_path: Path, func_name: str = "") -> None:
        """Ensure the file exists."""
        if not file_path.exists():
            raise FileNotFoundError(f"Error in {func_name}: File not found at '{file_path}'. Please ensure the file exists.")

    @staticmethod
    def validate_output_extension(output_path: Path, allowed_extensions: list[str], func_name: str = "") -> None:
        """Ensure the file has one of the allowed extensions."""
        if output_path.suffix not in allowed_extensions:
            allowed_ext_str = ', '.join(allowed_extensions)
            raise ValueError(
                f"Error in {func_name}: Invalid file extension '{output_path.suffix}'. Allowed extensions: {allowed_ext_str}."
            )
        
    # Error Generators
    @staticmethod
    def generate_permission_error(task: str, path: Path, suggestion: str = "Check file permissions.") -> PermissionError:
        """Generates a custom PermissionError with a specific task and file path."""
        return PermissionError(f"Permission denied: Unable to {task} at '{path}'. {suggestion}")

    @staticmethod
    def generate_os_error(task: str, path: Path, suggestion: str = "Check disk space or path validity.") -> OSError:
        """Generates a custom OSError with specific task and file path."""
        return OSError(f"File system error: Could not {task} at '{path}'. {suggestion}")

    @staticmethod
    def generate_file_not_found_error(path: Path, suggestion: str = "Ensure the file or directory exists.") -> FileNotFoundError:
        """Generates a custom FileNotFoundError for missing files or directories."""
        return FileNotFoundError(f"File not found at '{path}'. {suggestion}")

    @staticmethod
    def generate_value_error(value_type: str, attribute_name: str, expected_types: str) -> ValueError:
        """Generates a custom ValueError for unsupported types."""
        return ValueError(f"Unsupported data type '{value_type}' for '{attribute_name}'. Expected {expected_types}.")

   # Database Export Strategy