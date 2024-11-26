import pandas as pd
import pytest

from standard_base.properties_calculators.calculation_validation_helper import ValidationHelper

# Move test from BaseStandardOperatorTest to ValidationHelper
# As Valiation has moved to a separate class, we need to update the test to reflect this change.

# Test validate_positive_number


def test_validate_positive_number_valid():
    """Test that valid positive numbers pass without error."""
    ValidationHelper.validate_positive_number(10, "test_var")
    ValidationHelper.validate_positive_number(5.5, "test_var")


def test_validate_positive_number_invalid():
    """Test that invalid numbers raise the correct error."""
    with pytest.raises(ValueError, match="test_var must be a positive float or int."):
        ValidationHelper.validate_positive_number(0, "test_var")
    with pytest.raises(ValueError, match="test_var must be a positive float or int."):
        ValidationHelper.validate_positive_number(-5, "test_var")
    with pytest.raises(ValueError, match="test_var must be a positive float or int."):
        ValidationHelper.validate_positive_number("string", "test_var")


def test_validate_positive_number_with_parent_func_name():
    """Test error message when parent_func_name is provided."""
    # Expect: test_var must be a positive float or int in function [test_func]. Received: -1
    with pytest.raises(ValueError, match=r".*test_var must be a positive float or int in function \[test_func\].*"):
        ValidationHelper.validate_positive_number(-1, "test_var", "test_func")


# Test validate_columns_exist


def test_validate_columns_exist_valid():
    """Test that DataFrames containing the required columns pass without error."""
    df1 = pd.DataFrame({"time": [1, 2], "value": [10, 20]})
    df2 = pd.DataFrame({"time": [1, 3], "value": [15, 30]})
    ValidationHelper.validate_columns_exist([df1, df2], ["time", "value"])


def test_validate_columns_exist_missing_column():
    """Test that missing columns raise the correct error and return the index of missing DataFrames."""
    df1 = pd.DataFrame({"time": [1, 2]})
    df2 = pd.DataFrame({"time": [1, 3], "value": [15, 30]})
    df1.name = "DF1"
    df2.name = "DF2"

    # Expected error message
    """
    The following DataFrames are missing columns:
        DF1 is missing columns: value
    """
    with pytest.raises(ValueError, match=r".*DF1 is missing columns.*"):
        ValidationHelper.validate_columns_exist([df1, df2], ["time", "value"])


def test_validate_columns_exist_no_name():
    """Test that unnamed DataFrames return their index in the error message."""
    df1 = pd.DataFrame({"time": [1, 2]})
    df2 = pd.DataFrame({"time": [1, 3], "value": [15, 30]})

    with pytest.raises(ValueError, match="DataFrame at index 0 is missing columns: value"):
        ValidationHelper.validate_columns_exist([df1, df2], ["time", "value"])
