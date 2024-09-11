from typing import TYPE_CHECKING, Union

import pandas as pd
from pint import UnitRegistry
from pydantic import ValidationError

from .validators import MechanicalTestDataTypes, MechanicalTestStandards, SampleProperties, validator_registry

# from standard_validator import MechanicalTestDataTypes, MechanicalTestStandards, SampleProperties, validator_registry


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
            MechanicalTestDataTypes.GENERAL.value: self.toplevel_window.general_data.get("data", None),
            MechanicalTestDataTypes.HYSTERESIS.value: self.toplevel_window.hysteresis_data.get("data", None),
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
                key = MechanicalTestDataTypes.GENERAL.value
            elif only_hysteresis_file_is_present:
                key = MechanicalTestDataTypes.HYSTERESIS.value
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

            # Currently only stress-strain data is supported for visualization
            # Since the program only plots stress-strain data
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
        try:
            self.valid_properties = SampleProperties(**self.properties)
            print(f"Sample properties are valid:\\{self.valid_properties}")
            return "all_properties"
        except ValidationError as e:
            name = self.properties.get("name", None)
            if name is None:
                return "none"
            return "name"

    def _check_for_ss_data(self, data: "pd.DataFrame") -> bool:
        required_columns = ["stress", "strain"]
        return all(col in data.columns for col in required_columns)

    def _recalculate_stress_strain(self, data: "pd.DataFrame") -> Union[pd.DataFrame, None]:
        required_columns = ["force", "displacement"]
        if all(col in data.columns for col in required_columns):
            return None
        else:
            area = self.valid_properties.area
            # (area)  mm^2 a pint quantity in a pydantic model
            cross_sectional_length = self.valid_properties.thickness
            # (cross section lenght ) mm pint quantity in a pydantic model
            data["stress"] = data["force"] / area.magnitude
            # Force is in N and area is in mm^2 -> stress is in N/mm^2 or MPa
            data["strain"] = data["displacement"] / cross_sectional_length.magnitude
            # Displacement is in mm and thickness is in mm -> strain is dimensionless
            return data

    def _validate_for_typical_sample(self):
        do_typical_sample = not self.valid_visualization_data
        if do_typical_sample:
            existing_specimen_properties = self._validate_properties()  # Returns 'name', 'all_properties', or 'none'
            if existing_specimen_properties != "all_properties":
                raise ValueError("All properties are required for typical sample submission.")

        standard = self.toplevel_window.standard

        validator = validator_registry.get(MechanicalTestStandards(standard), None)

        if validator is None:
            raise ValueError(f"Standard {standard} is not supported.")
        else:
            validator.validate(self.data, self.images, self.valid_properties)

    def _submission_rules_check(self):
        print("passing submission rules check.")
        pass

    def _submit_sample(self):
        if self.submission_callback:
            self.submission_callback(self.valid_data, self.valid_properties)
