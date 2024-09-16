import re
from collections import namedtuple
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Optional, Union

import pandas as pd
from pint import UnitRegistry
from pint.errors import UndefinedUnitError

ureg = UnitRegistry()

if TYPE_CHECKING:
    from pathlib import Path


class MechanicalTestDataPreprocessor:
    """
    A class for preprocessing mechanical testing data with functionalities for normalizing column names,
    converting units, and ensuring data consistency. It supports different input formats and applies
    transformations to standardize the data representation.

    Attributes:
        COLUMN_MAPPING (dict): A mapping of standardized column names to variations found in raw data.
        EXPECTED_UNITS (dict): A mapping of standardized column names to expected units.
        KNOWN_UNITS (dict): A mapping of column names to known units for manual extraction
        Q_ (function): A shortcut for creating quantities with units.

    Methods:
        __init__: Initializes the preprocessor with custom or default settings for column mapping and expected units.
        preprocess_data: Orchestrates the preprocessing of raw data lines or a pandas DataFrame.
        convert_lines_to_df: Converts a list of raw data lines into a pandas DataFrame.
        remap_df_columns: Remaps DataFrame columns to standardized names based on predefined mappings.
        _convert_units: Internal method to convert the units of DataFrame columns to expected standards.
    """

    # For Remapping columns to standard names
    DATA_COLUMN_MAPPING = {
        "stress": ["stress", "contrainte"],
        "strain": ["strain", "deformation"],
        "force": ["force", "load"],
        "displacement": [
            "displacement",
            "elongation",
            "extension",
        ],
        "time": ["time", "temps", "Time"],
    }  # To Do: Add Base units to column standard name

    SPECIMEN_COLUMN_MAPPING = {
        "specimenname": ["name", "nom", "nombre", "identifier", "id", "specimen", "sample"],
        "length": ["length", "longueur", "länge", "largo", "len", "long"],
        "width": ["width", "largeur", "breite", "ancho", "wid", "w"],
        "thickness": ["thickness", "épaisseur", "dicke", "espesor", "thick", "t", "cross_section"],
        "weight": ["weight", "poids", "gewicht", "peso", "wt", "wgt"],
    }
    SPECIMEN_REQUIRED_COLUMNS = ["specimenname", "length", "width", "thickness", "weight"]
    # For unit conversion
    Q_ = ureg.Quantity  # Shortcut for creating quantities with units
    unit_registry = ureg  # Pint unit registry
    
    EXPECTED_UNITS = {
        "stress": ureg.megapascal,
        "strain": ureg.dimensionless,
        "force": ureg.newton,
        "displacement": ureg.millimeter,
        "time": ureg.second,
    }
    # For mannual unit extraction if now found by regex
    KNOWN_UNITS = {
        "time": ["s", "ms", "min", "hr"],
        "force": ["N", "kN", "lbf"],
        "displacement": ["mm", "cm", "m"],
        "stress": ["Pa", "kPa", "MPa", "GPa"],
        "strain": ["%", "mm/mm", "in/in"],
    }

    def __init__(self, column_mapping: dict = None, expected_units: dict = None, known_units: dict = None):
        self.expected_units = expected_units or self.EXPECTED_UNITS
        self.column_mapping = column_mapping or self.DATA_COLUMN_MAPPING
        # Unit extraction regex pattern
        self.unit_extraction_pattern = re.compile(r"(.+?)\s*(?:\(|\[)([a-zA-Z%°]{1,3})(?:\)|\])?$")
        known_units = known_units or self.KNOWN_UNITS
        self.flat_known_units = set(unit for sublist in known_units.values() for unit in sublist)

    def preprocess_data(self, data_input: Union[pd.DataFrame, list[str]]) -> pd.DataFrame:
        """
        Orchestrates preprocessing steps for mechanical test data.
        This method accepts either a list of raw data lines or a pandas DataFrame. If a list of strings is provided,
        it will convert it into a DataFrame.

        Parameters:
            data_input (Union[pd.DataFrame, List[str]]): The input data source, either raw lines or a DataFrame.

        Returns:
            pd.DataFrame: The preprocessed DataFrame.
        """
        data = None

        if isinstance(data_input, list):
            data = self.convert_lines_to_df(data_input)
        elif isinstance(data_input, pd.DataFrame):
            data = data_input
        else:
            raise ValueError("Input data must be a list of strings or a pandas DataFrame.")

        unit_info = {col: self._parse_unit_from_column(col) for col in data.columns}
        normalized_df = self.remap_df_columns(data, self.column_mapping)
        data = self._convert_units(normalized_df, unit_info)
        return data

    @staticmethod
    def convert_lines_to_df(data: list[str]) -> pd.DataFrame:
        """
        Different data formats require different methods to convert them into a DataFrame.
        Thus a factory method is used to adpat to the different formats.
        """
        cleaner = MTDataCoercer.create(CoercerFormats.DEFAULT, config=CoercerFormats.DEFAULT.value)
        df = cleaner.create_df_from_txt_data(data)
        return df

    @staticmethod
    def remap_df_columns(df: pd.DataFrame, column_mapping: dict = None) -> pd.DataFrame:
        if column_mapping is None:
            column_mapping = MechanicalTestDataPreprocessor.DATA_COLUMN_MAPPING

        df = df.copy()
        # Remap the columns
        remapped_columns = {}
        for standard_name, variations in column_mapping.items():
            for variation in variations:
                matching_columns = [col for col in df.columns if variation in col.lower()]
                if matching_columns:
                    remapped_columns[matching_columns[0]] = standard_name
                    break

        return df.rename(columns=remapped_columns)

    @staticmethod
    def validate_columns(df: pd.DataFrame, column_mapping: dict = None, required_columns: dict = None) -> Optional[str]:
        if df.empty:
            return "The data frame is empty."

        df.columns = [col.strip().lower() for col in df.columns]  # Normalize column names for easier comparison

        if column_mapping is None:
            column_mapping = MechanicalTestDataPreprocessor.SPECIMEN_COLUMN_MAPPING

        if required_columns is None:
            required_columns = MechanicalTestDataPreprocessor.SPECIMEN_REQUIRED_COLUMNS

        missing_columns = [
            col for col in required_columns if not any(c.lower() in df.columns for c in column_mapping[col])
        ]
        if missing_columns:
            return f"Missing required columns: {', '.join(missing_columns)}"
        return None  # Return None if no errors

    def _convert_units(self, df: pd.DataFrame, unit_info: dict[str, tuple[str, Optional[str]]]) -> pd.DataFrame:
        df = df.copy()
        pint_quantity = None
        for original_name, (parsed_name, unit) in unit_info.items():
            if not unit:
                continue
            pint_quantity = self._parse_str_unit_to_pint(unit)
            expected_unit = self.expected_units.get(parsed_name)
            if not expected_unit or (
                isinstance(pint_quantity, UnitRegistry.Quantity) and pint_quantity.units == expected_unit
            ):  # might want to change to pint Quantity instead of Unit
                continue

            conversion_factor = self._get_conversion_factor(unit, expected_unit)
            df[parsed_name] *= conversion_factor
            print(
                f"Converted {original_name} from [{unit}] to [{str(expected_unit)}] using the conversion factor {conversion_factor} for the normalized column {parsed_name}"
            )
        return df

    @lru_cache(maxsize=10)
    def _parse_str_unit_to_pint(self, unit: str) -> Optional[UnitRegistry.Quantity]:
        try:
            return ureg(unit)
        except UndefinedUnitError as e:
            print(f"Unit parsing failed: {unit} with error {e}")

    @lru_cache(maxsize=128)
    def _get_conversion_factor(self, current_unit: UnitRegistry.Unit, target_unit: UnitRegistry.Unit) -> float:
        try:
            return self.Q_(1, current_unit).to(target_unit).magnitude
        except UndefinedUnitError as e:
            print(f"Conversion factor calculation failed: {current_unit} to {target_unit} with error {e}")
            return 1

    @lru_cache(maxsize=128)
    def _parse_unit_from_column(self, column: str) -> tuple[str, Optional[str]]:
        # Try to match the column name to the regex pattern
        match = self.unit_extraction_pattern.match(column)
        if match:
            name, unit = match.groups()
            # Check if the extracted unit is known
            if unit in self.flat_known_units:
                return (name.strip(), unit)
            else:
                return (name.strip(), None)
        else:
            # Split the column name by spaces to check if the last part is a known unit
            parts = column.split()
            if parts and parts[-1] in self.flat_known_units:
                name = " ".join(parts[:-1])
                unit = parts[-1]
                return (name, unit)
            else:
                return (column, None)

    @staticmethod
    def _parse_unit_from_df_column(
        dataframe: pd.DataFrame, pattern: re.Pattern = None, known: dict = None
    ) -> list[tuple[str, Optional[str]]]:
        # Regex pattern to extract units within parentheses or square brackets
        pattern = pattern or MechanicalTestDataPreprocessor.unit_extraction_pattern

        known_units = known or MechanicalTestDataPreprocessor.KNOWN_UNITS
        # Flatten the list of known units into a set for faster membership testing
        flat_known_units = set(unit for sublist in known_units.values() for unit in sublist)

        result = []
        for column in dataframe.columns:
            match = pattern.match(column)
            if match:
                name, unit = match.groups()
                result.append((name.strip(), unit))
            else:
                parts = column.split()
                if parts[-1] in flat_known_units:
                    name = " ".join(parts[:-1])
                    unit = parts[-1]
                    result.append((name, unit))
                else:
                    result.append((column, None))
        return result


# Configuration named tuple for data cleaner settings
RawDataConfig = namedtuple(
    "RawDataConfig",
    ["headers_of_interest", "header_row_offset", "unit_row_offset", "data_start_offset", "marker", "invalid_data"],
)


# Enum to store standard configurations
class CoercerFormats(Enum):
    DEFAULT = RawDataConfig(
        headers_of_interest=["Time", "Force", "Displacement"],
        header_row_offset=1,
        unit_row_offset=2,
        data_start_offset=3,
        marker="Data Acquisition",
        invalid_data=["Data Acquisition"],
    )


# Base coercer class
class MTDataCoercer:
    registry = {}  # Class registry

    @classmethod
    def register(cls, key):
        """A decorator to register classes with a specific configuration key"""

        def decorator(klass):
            cls.registry[key] = klass
            return klass

        return decorator

    @classmethod
    def create(cls, key, *args, **kwargs):
        """Create an instance of a class based on a given configuration key"""
        if key in cls.registry:
            return cls.registry[key](*args, **kwargs)
        else:
            raise ValueError(f"No class found for {key}")


@MTDataCoercer.register(CoercerFormats.DEFAULT)
class TextDataCleaner:
    def __init__(self, config: RawDataConfig):
        self.config = config
        self.marker = config.marker
        self.invalid_data = config.invalid_data

    def create_df_from_txt_data(self, data) -> pd.DataFrame:
        marker_row = self._find_marker_row(data, self.marker)
        headers, units = self._extract_headers_and_units(data, marker_row)
        return self._extract_data_rows(data, marker_row, headers)

    def _find_marker_row(self, data, marker):
        for i, line in enumerate(data):
            if marker in line:
                return i
        raise ValueError(f"Marker '{marker}' not found in the data.")

    def _extract_headers_and_units(self, data, marker_row):
        """Extract headers and units based on the configuration offsets."""
        headers_row = data[marker_row + self.config.header_row_offset].split()
        headers = [header for header in headers_row if header in self.config.headers_of_interest]
        units = data[marker_row + self.config.unit_row_offset].split()
        return headers, units

    def _extract_data_rows(self, data, marker_row, headers):
        """Extract data rows starting from a specific offset from the marker_row."""
        data_rows = []
        for line in data[marker_row + self.config.data_start_offset :]:
            if any(line.startswith(invalid) for invalid in self.invalid_data):
                continue  # Skip this iteration if the line starts with any invalid data marker
            if line.strip():  # Check if the line is not empty
                data_rows.append(line.split()[: len(headers)])
        return pd.DataFrame(data_rows, columns=headers)


if __name__ == "__main__":
    import os
    import sys

    # Check if the script is running from the current file or the other toplevel path
    if os.path.abspath(__file__) == os.path.abspath(sys.argv[0]):
        file_path = "specimen.dat"
    else:
        file_path = os.path.join("toplevel_create_sample", "specimen.dat")

    with open(file_path, "r") as file:
        data = file.readlines()

    cleaner = MTDataCoercer.create(CoercerFormats.DEFAULT, config=CoercerFormats.DEFAULT.value)
    print(cleaner.config)
    df = cleaner.create_df_from_txt_data(data)

    print(f"The first 5 from the dataframe: \n{df.head()}")  # The first 5 from the dataframe:
    print(f"The last 5 from the dataframe: \n{df.tail()}")  # The last 5 from the dataframe:
    print(f"The shape of the dataframe: \n{df.shape}")  # The shape of the dataframe:
    print("Now double check the data to ensure it's correct.")  # Now double check the data to ensure it's correct.

    # Test the MechanicalTestDataPreprocessor class

    # Input is already a DataFrame
    input_df = pd.DataFrame(
        {"force (kN)": [100, 200], "strain (%)": [0.1, 0.2], "time min": [10, 20], "displacement [cm]": [1, 2]}
    )
    preprocessor = MechanicalTestDataPreprocessor()

    result_df = preprocessor.preprocess_data(input_df)

    print(f"Preprocessed DataFrame:\n{result_df}")
