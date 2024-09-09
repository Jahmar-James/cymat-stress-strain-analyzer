from collections import namedtuple
from enum import Enum
from typing import Callable, Optional, Union

import pandas as pd
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
        global validator_registry
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
    GENERAL_PRELIMINARY = "(General (Preliminary)"
    CYMAT_ISO13314_2011 = "Cymat_ISO13314-2011"

    # Missing values check casefold of the str enum value
    @classmethod
    def _missing_(cls, value: str):
        value = value.casefold()
        for standard in cls:
            if value == standard.value.casefold():
                return standard
        return None


class IntervalRequirements(Enum):
    CONSECUTIVE_INTERVAL = "consecutive_interval"
    SAMPLE_FREQUENCY = "sample_frequency"
    TOLERANCE = "tolerance"
    THRESHOLD = "threshold"


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
        self.sample_properties_validation_methods: list[Callable] = []
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

        # Validate sample properties
        if sample_properties and self.sample_properties_validation_methods:
            for validate in self.sample_properties_validation_methods:
                result = validate(sample_properties)
                results.append(result)

                if result.update_data:
                    self.validated_sample_properties = result.data

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
        consecutive_intervals_nt = self._validate_consecutive_intervals(data, column_requirements)
        sample_frequency_nt = self._validate_sample_frequency(data, column_requirements)
        return [consecutive_intervals_nt, sample_frequency_nt]

    def _validate_consecutive_intervals(
        self,
        data: "pd.DataFrame",
        column_requirements: dict,
        sample_size: int = 100,
        tolerance: tuple = (0.9, 1.1),
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

                upper_bound = target_interval * upper_tolerance
                lower_bound = target_interval * lower_tolerance

                if requirements.get(IntervalRequirements.THRESHOLD.value, False):
                    if (intervals > upper_bound).any():
                        invalid_columns.append(
                            f"{column.upper()} ({intervals.max():.4f} interval) Threshold: {upper_bound}"
                        )
                else:
                    if not intervals.between(lower_bound, upper_bound).all():
                        invalid_columns.append(
                            f"{column.upper()} (Avg. {intervals.mean():.4f} interval) Bounds: {lower_bound} - {upper_bound}"
                        )

        if invalid_columns:
            return validation_result(
                valid=False,
                error_message=f"Data's consecutive points in columns {', '.join(invalid_columns)} does not meet the requirement",
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

                upper_bound = target_frequency * upper_tolerance
                lower_bound = target_frequency * lower_tolerance

                if requirements.get(IntervalRequirements.THRESHOLD.value, False):
                    # Higher frequency is better as there is more points than required
                    if (actual_frequency < lower_bound).any():
                        invalid_columns.append(
                            f"{column.upper()} ({actual_frequency:.2f} Hz) Threshold: {lower_bound} Hz"
                        )
                else:
                    if not (lower_bound <= actual_frequency <= upper_bound):
                        invalid_columns.append(
                            f"{column.upper()} ({actual_frequency:.2f} Hz) Bounds: {lower_bound} - {upper_bound} Hz"
                        )

        if invalid_columns:
            return validation_result(
                valid=False,
                error_message=f"Data's frequency in columns {', '.join(invalid_columns)} does not meet the required interval",
                data=None,
                update_data=False,
            )
        return validation_result(valid=True, error_message="", data=None, update_data=False)


if __name__ == "__main__":
    # Test the SampleProperties model
    sample = SampleProperties(name="Test Sample", length=10, width=5, thickness=2, density=1, weight=50)
    print(sample)
    print(sample.area)
    print(sample.model_dump())
    print(sample.model_dump_json())