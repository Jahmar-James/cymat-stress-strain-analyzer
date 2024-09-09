import traceback
from typing import TYPE_CHECKING, Annotated, Optional

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, ValidationInfo

from .standard_validator import (
    BaseStandardValidator,
    IntervalRequirements,
    MechanicalTestDataTypes,
    MechanicalTestStandards,
    register_validator,
    validation_result,
)

if TYPE_CHECKING:
    from .standard_validator import SampleProperties


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
                # Ensure time data point every 1 seconds(stanard unit), and sample frequency is 5 Hz within the first 100 points and no tolerance
                "time": {
                    IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0,
                    IntervalRequirements.SAMPLE_FREQUENCY.value: 5,
                    IntervalRequirements.THRESHOLD.value: True,
                    IntervalRequirements.TOLERANCE.value: (1, 1),
                },
                # Ensure displacements sample frequency is 5 Hz within the first 100 points and default tolerance
                "displacement": {
                    IntervalRequirements.SAMPLE_FREQUENCY.value: 5,
                    IntervalRequirements.THRESHOLD.value: True,
                },
                # Ensure strain data point are withn 1.0 (mm/mm) spacing
                "strain": {
                    IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0,
                    IntervalRequirements.THRESHOLD.value: True,
                },
            },
            MechanicalTestDataTypes.HYSTERESIS.value: {
                # Ensure time data point every 1 seconds(stanard unit), and sample frequency is 5 Hz within the first 100 points and no tolerance
                "time": {
                    IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0,
                    IntervalRequirements.SAMPLE_FREQUENCY.value: 5,
                    IntervalRequirements.THRESHOLD.value: True,
                    IntervalRequirements.TOLERANCE.value: (1, 1),
                },
                # Ensure displacements sample frequency is 5 Hz within the first 100 points and default tolerance
                "displacement": {
                    IntervalRequirements.SAMPLE_FREQUENCY.value: 5,
                    IntervalRequirements.THRESHOLD.value: True,
                },
                # Ensure strain data point are withn 1.0 (mm/mm) spacing
                "strain": {
                    IntervalRequirements.CONSECUTIVE_INTERVAL.value: 1.0,
                    IntervalRequirements.THRESHOLD.value: True,
                },
            },
        }

    @staticmethod
    def validate_general(data: "pd.DataFrame", data_type: str) -> validation_result:
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

    @staticmethod
    def validate_hysteresis(data: "pd.DataFrame", data_type: str) -> validation_result:
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

    @staticmethod
    def validate_sample_properties(sample_properties: Optional["SampleProperties"]) -> validation_result:
        """
        makes the sample properties are in the valid ranges
        Create a specific pydantic model for the standard
        Which will taken in the serialized prevalidated sample properties
        """
        if sample_properties is None:
            return validation_result(
                valid=False,
                error_message="Sample properties are None",
                data=None,
                update_data=False,
            )

        samlple_dim = Annotated[float, Field(gt=0, le=100)]  # Greater than 0 and less than or equal to 100 mm

        class VALIDSAMPLE(BaseModel):
            name: str
            length: samlple_dim
            width: samlple_dim
            thickness: samlple_dim
            area: float
            density: float = Field(gt=0, le=2.7)  # Greater than 0 and less than or equal to 2.7 g/cm^3 Alumium density

        try:
            valid_sample = VALIDSAMPLE(**sample_properties)
            return validation_result(True, "", data=valid_sample.dump(), update_data=False)
        except ValidationError as e:
            return validation_result(
                valid=False,
                error_message=f"Invalid sample properties. ValidationError: {e}",
                data=None,
                update_data=False,
            )


if __name__ == "__main__":
    pass
