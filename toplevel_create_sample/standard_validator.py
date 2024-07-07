import traceback
from collections import namedtuple
from enum import Enum
from tkinter import E
from turtle import up
from typing import TYPE_CHECKING, Callable, Optional, Union

import pandas as pd
from matplotlib.dates import SA
from pint import UnitRegistry
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, computed_field, field_validator


# Validation on Submission (Sample Properties and Adherence to selected  Standards)
class SampleProperties(BaseModel):
    name: str
    length: Union[UnitRegistry.Quantity, None]
    width: Union[UnitRegistry.Quantity, None]
    thickness: Union[UnitRegistry.Quantity, None]
    density: Union[UnitRegistry.Quantity, None]
    weight: Union[UnitRegistry.Quantity, None]

    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

    def __repr__(self):
        return f"<SampleProperties(name={self.name}, density={self.density}, length={self.length})>"

    @field_validator("length", "width", "thickness", "weight", mode="after")
    @classmethod
    def validate_positive(cls, value, info: ValidationInfo):
        if value.magnitude <= 0:
            raise ValueError(f"Value must be positive: {value}")
        return value

    @computed_field(return_type=UnitRegistry.Quantity)
    def area(self) -> UnitRegistry.Quantity:
        if self.length and self.width:
            return self.length * self.width


# Registry for validators
validator_registry = {}


# Decorator for registering validators
def register_validator(standard) -> Callable:
    def decorator(cls):
        validator_registry[standard] = cls()
        return cls

    return decorator


validation_result = namedtuple("validation_result", ["valid", "error_message", "data", "update_data"])
# validation_result: (bool, str, Optional[pd.DataFrame], bool)


class MechanicalTestDataTypes(Enum):
    GENERAL = "general"
    HYSTERESIS = "hysteresis"
    FATIGUE = "fatigue"
    SAMPLE_PROPERTIES = "sample_properties"


class MechanicalTestStandards(Enum):
    GENERAL_PRELIMINARY = "(General (Preliminary))"
    CYMAT_ISO13314_2011 = "Cymat_ISO13314-2011"


class IntervalRequirements(Enum):
    CONSECUTIVE_INTERVAL = "consecutive_interval"
    SAMPLE_FREQUENCY = "sample_frequency"
    TOLERANCE = "tolerance"
    UPPER_BOUND_ONLY = "upper_bound_only"


class BaseStandardValidator:
    def __init__(self):
        """
        Initializes a base class for creating specific StandardValidator classes. This class includes structures
        to manage data validation plans, image processing plans, and specific validation requirements for different
        types of data. It is intended to be inherited by specific validator implementations that define the actual
        validation logic for each data type and image processing requirement.

        Attributes:
            data_validation_methods (dict[str, list[Callable]]):
                A dictionary mapping each unique data type identifier (e.g., 'general', 'hysteresis') to a list of
                Callable functions. These functions are designed to validate and potentially modify the data. Each
                Callable should return a `validation_result` namedtuple, which includes information on data validity,
                any error messages, potentially modified data, and a flag indicating whether the data was updated.

                Example:
                    self.data_validation_methods = {
                        'general': [self.validate_general],
                        'hysteresis': [self.validate_hysteresis]
                    }

                Callable Signature:
                    Callable(data: pd.DataFrame) -> validation_result

            image_validation_methods (list[Callable]):
                A list of Callable functions for validating and processing images. These functions should return a
                `validation_result` namedtuple, similar to data validators.

                Callable Signature:
                    Callable(images: list) -> validation_result

            column_name_requirements (dict[str, dict[str, list[str]]]):
                A dictionary mapping a data type to another dictionary. This nested dictionary maps column names to
                lists of required values that are valid for these columns, ensuring that data sets contain all necessary
                columns with valid entries.

                Example:
                    self.column_name_requirements ={
                        'general': ['Time', 'Force', 'Displacement'],
                        'hysteresis': ['Time', 'Force', 'Displacement']
                    }

            column_interval_requirements (dict[str, dict[str, float]]):
                A dictionary mapping a data type to another dictionary specifying the required interval between data
                points in specified columns. This helps ensure data consistency in time or measurement intervals.

                Example:
                     self.column_interval_requirements = {
                        'general': {
                            'time': 0.1,  # 10 Hz, expecting a data point every 0.1 seconds
                            'displacement': 5  # Expecting 10 points every 5 cm
                        },
                        'hysteresis': {
                            'time': 0.1  # Also 10 Hz for hysteresis data
                        }
                    }

            valid_data (pd.DataFrame or None):
                Holds the validated and potentially modified data if updates are required during validation. Defaults to
                None until updates are made through validation.

            valid_images (list or None):
                Holds the validated and potentially modified images if updates are required during validation. Defaults
                to None until updates are made through validation.

            error_messages (list[str]):
                A list to store error messages generated during the validation process.

            Additional Notes:
                - If a standard needs to carry over data from one validation step to another, store the intermediary
                  data in self.data. Once validation is complete, store the final validated data in self.valid_data.
        """
        self.data_validation_methods: dict[str, list[Callable]] = {}
        self.image_validation_methods: list[Callable] = []
        self.column_name_requirements: dict[str, dict[str, list[str]]] = {}
        self.column_interval_requirements: dict[str, dict[str, int]] = {}
        self.valid_data = None
        self.valid_images = None
        self.error_messages = None

    def validate(
        self,
        data_dict: dict[str, "pd.DataFrame"],
        images: Optional[list] = None,
        sample_properties=Optional["SampleProperties"],
    ) -> bool:
        results: list["validation_result"] = []

        for data_type, data in data_dict.items():
            # Validate data is present and correct type
            if data_type in self.data_validation_methods:
                for validate in self.data_validation_methods[data_type]:
                    result = validate(data, data_type)
                    results.append(result)

                    if result.update_data:
                        self.validated_data = result.data

            if data is not None:
                # Validate column names
                if data_type in self.column_name_requirements:
                    results.append(self._validate_column_name(data, self.column_name_requirements[data_type]))

                # Validate data intervals (Frequency)
                if data_type in self.column_interval_requirements:
                    nts = self._validate_data_freq(data, self.column_interval_requirements[data_type])
                    results.extend(nts)

        # Validate images
        if images and self.image_validation_methods:
            for validate in self.image_validation_methods:
                result = validate(images)
                results.append(result)

                if result.update_data:
                    self.validated_images = result.data

        self.error_messages = [result.error_message for result in results if not result.valid]

        return all([result.valid for result in results])

    def _validate_column_name(self, data: "pd.DataFrame", required_columns: list) -> list[validation_result]:
        missing_columns = [column for column in required_columns if column not in data.columns]
        if missing_columns:
            return validation_result(False, f"Missing required columnd: {missing_columns}", data, False)
        return validation_result(valid=True, error_message="", data=None, update_data=False)

    def _validate_data_freq(self, data: "pd.DataFrame", column_requirements: dict) -> validation_result:
        """
        Validates that the intervals between data points in a specified column are consistent with a target interval.

        """
        missing_columns = [column for column in column_requirements if column not in data.columns]
        if missing_columns:
            return validation_result(
                valid=False,
                error_message=f"Undetermined frequency: Column {missing_columns} does not exist",
                data=None,
                update_data=False,
            )
        consecutive_intervals_nt = self._validate_consecutive_intervals(
            data, self.column_interval_requirements["consecutive_interval"]
        )
        sample_frequency_nt = self._validate_sample_frequency(
            data, self.column_interval_requirements["sample_frequency"]
        )
        return [consecutive_intervals_nt, sample_frequency_nt]

    def _validate_consecutive_intervals(
        self,
        data: "pd.DataFrame",
        column_requirements: dict,
        sample_size: int = 100,
        tolerance: tuple = (0.9, 1.1),
        upper_bound_only: bool = False,
    ) -> validation_result:
        """
        Validates that the intervals between consecutive data points in a specified column are consistent with a target interval.
        """
        invalid_columns = []
        for column, requirements in column_requirements.items():
            if IntervalRequirements.CONSECUTIVE_INTERVAL.value in requirements and pd.api.types.is_numeric_dtype(
                data[column]
            ):
                intervals = data[column].diff().iloc[1:sample_size]  # calculate differences between consecutive entries
                target_interval = requirements[IntervalRequirements.CONSECUTIVE_INTERVAL.value]
                lower_tolerance, upper_tolerance = requirements.get("tolerance", tolerance)

                if upper_bound_only:
                    if not intervals.between(target_interval, target_interval * upper_tolerance).all():
                        invalid_columns.append(
                            f"{column} ({intervals.max()} interval) at the index {intervals.idxmax()}"
                        )
                else:
                    if not intervals.between(
                        target_interval * lower_tolerance, target_interval * upper_tolerance
                    ).all():
                        invalid_columns.append(f"{column} ({intervals.mean()} interval)")

        if invalid_columns:
            return validation_result(
                valid=False,
                error_message=f"Data frequency in columns {', '.join(invalid_columns)} does not meet the required interval",
                data=None,
                update_data=False,
            )
        return validation_result(valid=True, error_message="", data=None, update_data=False)

    def _validate_sample_frequency(
        self,
        data: "pd.DataFrame",
        column_requirements: dict,
        points: int = 100,
        tolerance: tuple = (0.9, 1.1),
        upper_bound_only: bool = False,
    ) -> validation_result:
        """
        Validates that the data frequency in a specified column meets the required interval.
        """
        invalid_columns = []
        for column, requirements in column_requirements.items():
            if IntervalRequirements.SAMPLE_FREQUENCY.value in requirements and pd.api.types.is_numeric_dtype(
                data[column]
            ):
                duration = data[column].iloc[points - 1] - data[column].iloc[0]
                actual_frequency = (points - 1) / duration
                target_frequency = requirements[IntervalRequirements.SAMPLE_FREQUENCY.value]
                lower_tolerance, upper_tolerance = requirements.get(IntervalRequirements.TOLERANCE.value, tolerance)

                if upper_bound_only:
                    if not (target_frequency <= actual_frequency <= target_frequency * upper_tolerance):
                        invalid_columns.append(f"{column} ({actual_frequency:.2f} Hz)")
                else:
                    if not (
                        target_frequency * lower_tolerance <= actual_frequency <= target_frequency * upper_tolerance
                    ):
                        invalid_columns.append(f"{column} ({actual_frequency:.2f} Hz)")

        if invalid_columns:
            return validation_result(
                valid=False,
                error_message=f"Data frequency in columns {', '.join(invalid_columns)} does not meet the required interval",
                data=None,
                update_data=False,
            )
        return validation_result(valid=True, error_message="", data=None, update_data=False)


@register_validator(MechanicalTestStandards.GENERAL_PRELIMINARY)
class GeneralPreliminaryValidator(BaseStandardValidator):
    def __init__(self):
        super().__init__()
        pass
        # raise NotImplementedError("General Preliminary validation not implemented")


@register_validator(MechanicalTestStandards.CYMAT_ISO13314_2011)
class CymatISO133142011Validator(BaseStandardValidator):
    """
    Assume the data is a DataFrame, convert units, normalized columns, and type checked:

    Will now check the data for the following:
    1. necessary columns are present for given types
    2. validate the data frequency for each column based on the standard

    - no image validation needed
    """

    def __init__(self):
        super().__init__()
        self.data_validation_methods = {
            MechanicalTestDataTypes.GENERAL.value: [self.validate_general],
            MechanicalTestDataTypes.HYSTERESIS.value: [self.validate_hysteresis],
        }

        self.column_name_requirements = {
            MechanicalTestDataTypes.GENERAL.value: ["time", "force", "displacement"],
            MechanicalTestDataTypes.HYSTERESIS.value: ["time", "force", "displacement"],
        }

        self.column_interval_requirements = {
            MechanicalTestDataTypes.GENERAL.value: {
                "time": {IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0},
                "displacement": {IntervalRequirements.SAMPLE_FREQUENCY.value: 5},
                "strain": {
                    IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0,
                    IntervalRequirements.UPPER_BOUND_ONLY.value: True,
                },
            },
            MechanicalTestDataTypes.HYSTERESIS.value: {"time": 100},
            "displacement": {IntervalRequirements.SAMPLE_FREQUENCY.value: 5},
            "strain": {IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0},
        }

    def validate_general(self, data: "pd.DataFrame", data_type: str) -> validation_result:
        try:
            assert data is not None, "Data is None"
            assert isinstance(data, pd.DataFrame), "Data is not a DataFrame"
            assert not data.empty, "DataFrame is empty"
            assert (
                data_type == MechanicalTestDataTypes.GENERAL.value
            ), f"Data type is not {MechanicalTestDataTypes.GENERAL.value}"
            return validation_result(True, "", None, False)
        except AssertionError as e:
            return validation_result(
                valid=False,
                error_message=f"Invalid {data_type} data. AssertionError: {e}",
                data=None,
                update_data=False,
            )
        except Exception as e:
            return validation_result(
                valid=False,
                error_message=f"Unexpected error: {e}\n{traceback.format_exc()}",
                data=None,
                update_data=False,
            )

    def validate_hysteresis(self, data: "pd.DataFrame", data_type: str) -> validation_result:
        try:
            assert data is not None, "Data is None"
            assert isinstance(data, pd.DataFrame), "Data is not a DataFrame"
            assert not data.empty, "DataFrame is empty"
            assert (
                data_type == MechanicalTestDataTypes.HYSTERESIS.value
            ), f"Data type is not {MechanicalTestDataTypes.HYSTERESIS.value}"
            return validation_result(True, "", None, False)
        except AssertionError as e:
            return validation_result(
                valid=False,
                error_message=f"Invalid {data_type} data. AssertionError: {e}",
                data=None,
                update_data=False,
            )
        except Exception as e:
            return validation_result(
                valid=False,
                error_message=f"Unexpected error: {e}\n{traceback.format_exc()}",
                data=None,
                update_data=False,
            )


if __name__ == "__main__":
    # Test the SampleProperties model
    sample = SampleProperties(name="Test Sample", length=10, width=5, thickness=2, density=1, weight=50)
    print(sample)
    print(sample.area)
    print(sample.model_dump())
    print(sample.model_dump_json())

    # # Test the GeneralPreliminaryValidator
    # general_validator = validator_registry[MechanicalTestStandards.GENERAL_PRELIMINARY]
    # print(general_validator.validate({MechanicalTestDataTypes.GENERAL: pd.DataFrame()}))

    # # Test the CymatISO133142011Validator
    # cymat_validator = validator_registry[MechanicalTestStandards.CYMAT_ISO13314_2011]
    # print(cymat_validator.validate({MechanicalTestDataTypes.GENERAL: pd.DataFrame(), MechanicalTestDataTypes.HYSTERESIS: pd.DataFrame()}))    # print(general_validator.validate({MechanicalTestDataTypes.GENERAL: pd.DataFrame()}))

    # # Test the CymatISO133142011Validator
    # cymat_validator = validator_registry[MechanicalTestStandards.CYMAT_ISO13314_2011]
    # print(cymat_validator.validate({MechanicalTestDataTypes.GENERAL: pd.DataFrame(), MechanicalTestDataTypes.HYSTERESIS: pd.DataFrame()}))