import pandas as pd
import pytest

from .standard_validator import CymatISO133142011Validator, MechanicalTestDataTypes


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
def validator() -> CymatISO133142011Validator:
    return CymatISO133142011Validator()


def test_valid_general_data(validator, valid_general_data) -> None:
    result = validator.validate_general(valid_general_data, MechanicalTestDataTypes.GENERAL.value)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None  # Return None for valid data that does not need to be updated
    assert not result.update_data


def test_invalid_general_data(validator, invalid_data) -> None:
    result = validator.validate_general(invalid_data, MechanicalTestDataTypes.GENERAL.value)
    assert not result.valid
    assert "AssertionError" in result.error_message


def test_valid_hysteresis_data(validator, valid_hysteresis_data) -> None:
    result = validator.validate_hysteresis(valid_hysteresis_data, MechanicalTestDataTypes.HYSTERESIS.value)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_invalid_hysteresis_data(validator, invalid_data) -> None:
    result = validator.validate_hysteresis(invalid_data, MechanicalTestDataTypes.HYSTERESIS.value)
    assert not result.valid
    assert "AssertionError" in result.error_message


def test_validate_column_name_success(validator: CymatISO133142011Validator, valid_general_data) -> None:
    required_columns = validator.column_name_requirements["general"]
    result = validator._validate_column_name(valid_general_data, required_columns)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_validate_column_name_missing_columns(validator: CymatISO133142011Validator, valid_general_data) -> None:
    required_columns = ["time", "force", "displacement", "missing_column"]
    result = validator._validate_column_name(valid_general_data, required_columns)
    assert not result.valid
    assert "Missing required columnd" in result.error_message
    assert result.data is valid_general_data
    assert not result.update_data


def test_validate_consecutive_intervals_success(validator: CymatISO133142011Validator, valid_general_data) -> None:
    column_requirements = {
        "time": {"consecutive_interval": 1.0},
    }
    result = validator._validate_consecutive_intervals(valid_general_data, column_requirements)
    assert result.valid
    assert result.error_message == ""
    assert result.data is None
    assert not result.update_data


def test_validate_consecutive_intervals_incorrect(
    validator: CymatISO133142011Validator,
) -> None:
    data = {
        "time": [0, 1, 2, 4, 5, 7],  # intervals are not consistent with 1.0
        "force": [0, 10, 20, 30, 40, 50],
        "displacement": [0, 1, 2, 3, 4, 5],
    }
    df = pd.DataFrame(data)
    column_requirements = {
        "time": {"consecutive_interval": 1.0},
    }
    result = validator._validate_consecutive_intervals(df, column_requirements)
    assert not result.valid
    assert r"time" in result.error_message  # why 1.4 double check and error message ( mean)
    assert result.data is None
    assert not result.update_data


def test_validate_sample_frequency_success(
    validator: CymatISO133142011Validator,
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


def test_validate_sample_frequency_incorrect(validator: CymatISO133142011Validator) -> None:
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
    assert "time (2.00 Hz)" in result.error_message
    assert result.data is None
    assert not result.update_data
