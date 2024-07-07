from typing import TYPE_CHECKING, Union

import pandas as pd
from mechanical_test_data_preprocessor import MechanicalTestDataPreprocessor
from pint import UnitRegistry
from pydantic import ValidationError
from standard_Cymat_validators import CymatISO133142011Validator
from standard_general_validator import GeneralPreliminaryValidator
from standard_validator import MechanicalTestDataTypes, MechanicalTestStandards, SampleProperties

if TYPE_CHECKING:
    from toplevel_create_sample.toplevel_create_sample import CreateSampleWindow


class ToplevelValidator:
    def __init__(self, toplevel: "CreateSampleWindow", submission_callback=None):
        self.toplevel_window = toplevel
        self.submission_callback = submission_callback
        self.data = {}
        self.valid_data = {}
        self.properties = None
        self.valid_properties = None
        self.valid_visualization_data = False

    def validate_all(self) -> bool:
        self._check_file_validity()
        self._load_data()
        self._validate_for_visualization()
        self._validate_for_typical_sample()
        self._submission_rules_check()
        self._submit_sample()

    def _check_file_validity(self):
        self.valid_general_file = self.toplevel_window.general_data_is_vaild.get()
        self.valid_hysteresis_file = self.toplevel_window.hysteresis_data_is_vaild.get()
        if not self.valid_general_file and not self.valid_hysteresis_file:
            raise ValueError("Atleast one data files are required for submission.")

    def _load_data(self):
        self.properties = self.toplevel_window.middle_frame.properties_frame.formatted_entry_values
        self.data = {
            "general": self.toplevel_window.general_data.get("data", None),
            "hysteresis": self.toplevel_window.hysteresis_data.get("data", None),
        }
        self.images = self.toplevel_window.image_data.get("data", None)
        self.do_recalculate_ss = self.toplevel_window.recalculate_toggle_var.get()
        self.standards = self.toplevel_window.standard

    def _validate_for_visualization(self):
        self.valid_visualization_data = False
        specimen_is_for_visualization = self.toplevel_window.visualize_specimen_toggle_var.get()
        if specimen_is_for_visualization:
            existing_specimen_properties = self._validate_properties()  # Returns 'name', 'all', or 'none'

            if existing_specimen_properties == "none":
                raise ValueError("Sample name is required for visualization.")

            both_files_are_present = self.valid_general_file and self.valid_hysteresis_file
            only_general_file_is_present = self.valid_general_file and not self.valid_hysteresis_file
            only_hysteresis_file_is_present = not self.valid_general_file and self.valid_hysteresis_file

            # if both are present use the general data
            if both_files_are_present or only_general_file_is_present:
                key = "general"
            elif only_hysteresis_file_is_present:
                key = "hysteresis"
            else:
                raise ValueError("General or hysteresis data is required for visualization.")

            selected_data_column_names = self.data[key].columns.tolist()

            working_data = self.data[key].copy()
            data_has_ss = self._check_for_ss_data(working_data)

            if not data_has_ss and not self.do_recalculate_ss:
                raise ValueError("If data has force and displacement, Turn on the recalculate toggle.")

            if self.do_recalculate_ss:
                recalculated_data = self._recalculate_stress_strain(working_data)
                if recalculated_data is not None:
                    self.data[key] = recalculated_data
                    selected_data_column_names = recalculated_data.columns.tolist()

            if existing_specimen_properties == "name" and all(
                x in selected_data_column_names for x in ["stress", "strain"]
            ):
                self.valid_visualization_data = True
                self.valid_data[key] = self.data[key]

            if existing_specimen_properties == "all_properties" and all(
                x in selected_data_column_names for x in ["force", "displacement"]
            ):
                self.valid_visualization_data = True
                self.valid_data[key] = self.data[key]

    def _validate_properties(self) -> str:
        # TODO Get precalculated properties from tkinter display ( Density, area.)
        try:
            self.valid_properties = SampleProperties(**self.properties)
            print(f"Visualization Sample properties are valid. {self.valid_properties}")
            return "all_properties"
        except ValidationError as e:
            name = self.properties.get("name", None)
            if name is None:
                return "none"
            return "name"

    def _check_for_ss_data(self, data: "pd.DataFrame"):
        required_columns = ["stress", "strain"]
        mapping = {
            "stress": ["stress", "contrainte"],
            "strain": ["strain", "deformation"],
        }
        msg = MechanicalTestDataPreprocessor.validate_columns(
            df=data, required_columns=required_columns, column_mapping=mapping
        )
        # Returns a error message if the required columns are not found
        # Thus if there is a message, the data is missing the required columns
        # We are Checking if the data is has the columns required for stress and strain
        if msg:
            return False  # data is missing stress and strain columns
        else:
            return True  # data has the required columns

    def _recalculate_stress_strain(self, data: "pd.DataFrame") -> Union[pd.DataFrame, None]:
        required_columns = ["force", "displacement"]
        mapping = {
            "force": ["force", "load"],
            "displacement": ["displacement", "elongation"],
        }
        msg = MechanicalTestDataPreprocessor.validate_columns(
            df=data, required_columns=required_columns, column_mapping=mapping
        )
        if msg:  # not found the required columns
            return None
        else:
            area = self.valid_properties.area  # mm^2 a pint quantity in a pydantic model
            cross_sectional_length = self.valid_properties.thickness  # mm pint quantity in a pydantic model
            data["stress"] = (
                data["force"] / area.magnitude
            )  # Force is in N and area is in mm^2 -> stress is in N/mm^2 or MPa
            data["strain"] = (
                data["displacement"] / cross_sectional_length.magnitude
            )  # Displacement is in mm and thickness is in mm -> strain is dimensionless
            return data

    def _validate_for_typical_sample(self):
        do_typical_sample = not self.valid_visualization_data
        if do_typical_sample:
            existing_specimen_properties = self._validate_properties()  # Returns 'name', 'all_properties', or 'none'
            if existing_specimen_properties != "all_properties":
                raise ValueError("All properties are required for typical sample submission.")

        standard = self.toplevel_window.standard
        # TODO: Factory pattern to create the correct validator based on the standard
        if standard == MechanicalTestStandards.CYMAT_ISO13314_2011.value:
            validator = CymatISO133142011Validator()
            validator.validate(self.data, self.images, self.valid_properties)
        elif standard == MechanicalTestStandards.GENERAL_PRELIMINARY.value:
            validator = GeneralPreliminaryValidator()
            validator.validate(self.data, self.images, self.valid_properties)
        else:
            raise ValueError(f"Standard {standard} is not supported.")

    def _submission_rules_check(self):
        print("passing submission rules check.")
        pass

    def _submit_sample(self):
        if self.submission_callback:
            self.submission_callback(self.valid_data, self.valid_properties)


# Pre-Proccessing data validator | Normalizing data into a df with standard column names
class DataValidator:
    """
    Class needs a new name
    it's roles Will be expanded to do the following tasks:
        - read with the file extension (csv, xlsx, txt, dat) and will return a pandas dataframe
        - normalize the column names to a standard format
        - do unit conversions if necessary otherwise assume the data is in the correct units

    These methods be used to automate pre-processing of data before submitssion validation.
    Give the user fast feedback on issues, and less wait for validation.
    """

    REQUIRED_COLUMNS = {
        "stress_strain": ["stress", "strain"],
        "displacement_force": ["displacement", "force"],
    }

    COLUMN_MAPPING = {
        "stress": ["stress", "contrainte"],
        "strain": ["strain", "deformation"],
        "force": ["force", "load"],
        "displacement": ["displacement", "elongation"],
        "Time": ["time", "temps", "Time"],
    }

    @staticmethod
    def validate_columns(data):
        if isinstance(data, pd.DataFrame) and not data.empty:
            print(f"Data has been imported successfully with the following columns: {list(data.columns)}")
            columns = [col.lower() for col in data.columns]
            if any(required in col for required in DataValidator.REQUIRED_COLUMNS["stress_strain"] for col in columns):
                print("Stress and strain data found.")
                return "stress_strain_df"
            elif any(
                required in col for required in DataValidator.REQUIRED_COLUMNS["displacement_force"] for col in columns
            ):
                print("Displacement and force data found. Further processing required.")
                return "displacement_force_df"
            else:
                raise ValueError("Data must contain columns related to either 'stress_strain' or 'displacement_force'")
        else:
            return None

    @staticmethod
    def remap_df_columns(df: pd.DataFrame, column_mapping: dict | None = None) -> pd.DataFrame:
        if column_mapping is None:
            column_mapping = DataValidator.COLUMN_MAPPING

        # Do necessary conversions
        original_columns = df.columns
        strain_variations = column_mapping.get("strain", [])
        for col in original_columns:
            if any(variation in col.lower() for variation in strain_variations) and "%" in col:
                df[col] = df[col].astype(float) / 100
                print(f"Converted strain from % to mm/mm for column: {col}")

        # Remap the columns
        remapped_columns = {}
        for standard_name, variations in column_mapping.items():
            for variation in variations:
                matching_columns = [col for col in df.columns if variation in col.lower()]
                if matching_columns:
                    remapped_columns[matching_columns[0]] = standard_name
                    break

        return df.rename(columns=remapped_columns)
