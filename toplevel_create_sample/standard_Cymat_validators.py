import traceback

import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, computed_field, field_validator
from standard_validator import (
    BaseStandardValidator,
    IntervalRequirements,
    MechanicalTestDataTypes,
    MechanicalTestStandards,
    register_validator,
    validation_result,
)


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
    pass