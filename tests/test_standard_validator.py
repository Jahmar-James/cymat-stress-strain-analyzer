import pandas as pd
import pytest
from pint import UnitRegistry

from standards.base.base_standard_validator import BaseStandardValidator, MechanicalTestDataTypes, SampleProperties
from standards.cymat_iso_13314_2011.validator import CymatISO133142011Validator


@pytest.fixture
def valid_general_data() -> pd.DataFrame:
    data = {"time": [0, 1, 2, 3, 4, 5], "force": [0, 10, 20, 30, 40, 50], "displacement": [0, 1, 2, 3, 4, 5]}
    return pd.DataFrame(data)


@pytest.fixture
def valid_hysteresis_data() -> pd.DataFrame:
    data = {"time": [0, 1, 2, 3, 4, 5], "force": [0, -10, 20, -30, 40, -50], "displacement": [0, 1, 2, 1, 0, -1]}
    return pd.DataFrame(data)


@pytest.fixture
def invalid_data() -> pd.DataFrame:
    return pd.DataFrame()


@pytest.fixture
def validator() -> BaseStandardValidator:
    return BaseStandardValidator()


@pytest.fixture
def validator_Cymat_ISO() -> CymatISO133142011Validator:
    return CymatISO133142011Validator()


# BaseStandardValidator tests


def test_validate_column_name_missing_columns(validator: BaseStandardValidator, valid_general_data) -> None:
    required_columns = ["time", "force", "displacement", "missing_column"]
    result = validator._validate_column_name(valid_general_data, required_columns)
    assert not result.valid
    assert "Missing required columnd" in result.error_message
    assert result.data is valid_general_data
    assert not result.update_data


def test_validate_consecutive_intervals_success(validator: BaseStandardValidator, valid_general_data) -> None:
    column_requirements = {
        "time": {"consecutive_interval": 1.0},
    }
    result = validator._validate_consecutive_intervals(valid_general_data, column_requirements)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_validate_consecutive_intervals_incorrect(validator: BaseStandardValidator) -> None:
    data = {
        "time": [0, 1, 2, 4, 5, 7],
        "force": [0, 10, 20, 30, 40, 50],
        "displacement": [0, 1, 2, 3, 4, 5],
    }
    # intervals are not consistent with 1.0 - 2 to 4 is 2.0 and 5 to 7 is 2.0
    # Difference = [1, 1, 2, 1, 2] - one less than the length of the data
    # Average of the difference is 1.4 = (1 + 2 + 1 + 2) / 4
    # There is some Tolerance in the data 90%-110% of expected value (1.0) = 0.9 to 1.1
    # 1.4 is not within the tolerance
    df = pd.DataFrame(data)
    column_requirements = {
        "time": {"consecutive_interval": 1.0},
    }
    result = validator._validate_consecutive_intervals(df, column_requirements)
    assert not result.valid
    assert r"time" in result.error_message.lower()
    assert "1.4" in result.error_message  # The average difference
    assert result.data is None
    assert not result.update_data


def test_validate_sample_frequency_success(
    validator: BaseStandardValidator,
) -> None:
    data = {
        "time": [i * 0.1 for i in range(250)],  # 10 Hz sampling frequency
        "force": [i for i in range(250)],
        "displacement": [i for i in range(250)],
    }
    df = pd.DataFrame(data)
    column_requirements = {
        "time": {"sample_frequency": 10.0},
    }
    result = validator._validate_sample_frequency(df, column_requirements, points=250)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_validate_sample_frequency_incorrect(validator: BaseStandardValidator) -> None:
    data = {
        "time": [0, 0.5, 1, 1.5, 2, 2.5],  # 2 Hz instead of 10 Hz
        "force": [0, 10, 20, 30, 40, 50],
        "displacement": [0, 1, 2, 3, 4, 5],
    }
    df = pd.DataFrame(data)
    column_requirements = {
        "time": {"sample_frequency": 10.0},
    }
    result = validator._validate_sample_frequency(df, column_requirements, points=6)
    assert not result.valid
    assert "time" in result.error_message.lower()  # This is the problem column
    assert "(2.00 Hz)" in result.error_message  # The actual sample frequency
    assert result.data is None
    assert not result.update_data
    assert result.data is None
    assert not result.update_data


# CymatISO133142011Validator tests
# As BaseStandardValidator is an abstract class, we cannot directly test it.
# We will test the concrete class CymatISO133142011Validator instead.
# As its the main Standard Our Company will be using.

# Limitation of BaseStandardValidator
# 1. Does not require a Column Names (Empty dict[str, dict[str, list[str]]] = {})
#    Thus Test missing a Required Column Name is implemented here in CymatISO133142011Validator
# 2. Does not not require a Sample Properties to be validated
#   Thus Test for Sample Properties is implemented here in CymatISO133142011Validator
# 3. Does not not require a general or hysteresis data to be validated
#   Thus Test for general and hysteresis data is implemented here in CymatISO133142011Validator


def test_valid_general_data(validator_Cymat_ISO: CymatISO133142011Validator, valid_general_data) -> None:
    result = validator_Cymat_ISO.validate_general(valid_general_data, MechanicalTestDataTypes.GENERAL.value)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None  # Return None for valid data that does not need to be updated
    assert not result.update_data


def test_invalid_general_data(validator_Cymat_ISO: CymatISO133142011Validator, invalid_data) -> None:
    result = validator_Cymat_ISO.validate_general(invalid_data, MechanicalTestDataTypes.GENERAL.value)
    assert not result.valid
    assert "AssertionError" in result.error_message


def test_valid_hysteresis_data(validator_Cymat_ISO: CymatISO133142011Validator, valid_hysteresis_data) -> None:
    result = validator_Cymat_ISO.validate_hysteresis(valid_hysteresis_data, MechanicalTestDataTypes.HYSTERESIS.value)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_invalid_hysteresis_data(validator_Cymat_ISO: CymatISO133142011Validator, invalid_data) -> None:
    result = validator_Cymat_ISO.validate_hysteresis(invalid_data, MechanicalTestDataTypes.HYSTERESIS.value)
    assert not result.valid
    assert "AssertionError" in result.error_message


def test_validate_column_name_success(validator_Cymat_ISO: CymatISO133142011Validator, valid_general_data) -> None:
    required_columns = validator_Cymat_ISO.column_name_requirements["general"]
    result = validator_Cymat_ISO._validate_column_name(valid_general_data, required_columns)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_validate_sample_properties_dict(validator_Cymat_ISO: CymatISO133142011Validator) -> None:
    sample_properties_dict = {
        "name": "Sample Name",
        "length": 10.0,
        "width": 5.0,
        "thickness": 2.0,
        "density": 1.0,
        "weight": 1.0,
    }
    result = validator_Cymat_ISO.validate_sample_properties(sample_properties_dict)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_validate_sample_properties_SampleProperties() -> None:
    ureg = UnitRegistry()
    sample_properties = SampleProperties(
        name="Sample Name",
        length=10.0 * ureg.mm,
        width=5.0 * ureg.mm,
        thickness=2.0 * ureg.mm,
        density=1.0 * ureg.g / ureg.cm**3,
        weight=1.0 * ureg.kg,
    )
    result = CymatISO133142011Validator.validate_sample_properties(sample_properties)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_invalid_sample_properties_weight(validator_Cymat_ISO: CymatISO133142011Validator) -> None:
    sample_properties_dict = {
        "name": "Sample Name",
        "length": 10.0,
        "width": 5.0,
        "thickness": 2.0,
        "density": 1.0,
        "weight": -1.0,  # Negative weight
    }
    result = validator_Cymat_ISO.validate_sample_properties(sample_properties_dict)
    assert not result.valid
    assert "weight" in result.error_message.lower()
    assert result.data is None
    assert not result.update_data


def test_invalid_sample_properties_density(validator_Cymat_ISO: CymatISO133142011Validator) -> None:
    sample_properties_dict = {
        "name": "Sample Name",
        "length": 10.0,
        "width": 5.0,
        "thickness": 2.0,
        "density": 3,  # higher than 2.7 g/cm^3
        "weight": 1.0,
    }
    result = validator_Cymat_ISO.validate_sample_properties(sample_properties_dict)
    assert not result.valid
    assert "density" in result.error_message.lower()
    assert result.data is None
    assert not result.update_data


def test_invalid_sample_properties_length(validator_Cymat_ISO: CymatISO133142011Validator) -> None:
    sample_properties_dict = {
        "name": "Sample Name",
        "length": 121.0,  # greater than 120 mm
        "width": 5.0,
        "thickness": 2.0,
        "density": 1.0,
        "weight": 1.0,
    }
    result = validator_Cymat_ISO.validate_sample_properties(sample_properties_dict)
    assert not result.valid
    assert "length" in result.error_message.lower()
    assert result.data is None
    assert not result.update_data
