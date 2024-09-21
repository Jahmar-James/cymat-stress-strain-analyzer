import numpy as np
import pandas as pd
import pytest

from standards.base.base_standard_operator import BaseStandardOperator


# Fixture for typical input data
@pytest.fixture
def typical_data() -> pd.Series:
    """Fixture for typical input values."""
    return pd.Series([100, 150, 200], name="force")  # Forces in Newtons


@pytest.fixture
def large_negative_data() -> pd.Series:
    """Fixture for input values where mean stress is negative."""
    return pd.Series([-100, -150, -200], name="force")  # Negative forces


@pytest.fixture
def mixed_data() -> pd.Series:
    """Fixture for input values with both positive and negative forces."""
    return pd.Series([-100, 150, -200], name="force")  # Mixed forces


# BaseStandardOperator test calculate_stress
# Test 1: Basic functionality
def test_calculate_stress_basic(typical_data):
    """Test stress calculation for typical values."""
    result = BaseStandardOperator.calculate_stress(typical_data, area=10.0)
    expected = pd.Series(
        [10.0, 15.0, 20.0], name="force"
    )  # Expected stress = force / area  - will be a float because of area
    pd.testing.assert_series_equal(result, expected)


# Test 2: With conversion factor
def test_calculate_stress_with_conversion(typical_data):
    """Test stress calculation with a conversion factor."""
    result = BaseStandardOperator.calculate_stress(typical_data, area=10.0, conversion_factor=2.0)
    expected = pd.Series([20.0, 30.0, 40.0], name="force")  # Expected stress with conversion factor
    pd.testing.assert_series_equal(result, expected)


# Test 3: Inversion check for compression (negative stress values)
def test_calculate_stress_inversion(large_negative_data):
    """Test stress inversion for negative stress values."""
    result = BaseStandardOperator.calculate_stress(large_negative_data, area=10.0)
    expected = pd.Series([10.0, 15.0, 20.0], name="force")  # Expected inverted stress for negative values
    pd.testing.assert_series_equal(result, expected)


# Test 4: No inversion when inversion_check is False
def test_calculate_stress_no_inversion(large_negative_data):
    """Test no inversion when inversion_check is False."""
    result = BaseStandardOperator.calculate_stress(large_negative_data, area=10.0, inversion_check=False)
    expected = pd.Series([-10.0, -15.0, -20.0], name="force")  # No inversion expected
    pd.testing.assert_series_equal(result, expected)


# Test 5: Mixed forces with inversion check
def test_calculate_stress_mixed_data_inversion(mixed_data):
    """Test stress calculation for mixed positive and negative forces."""
    result = BaseStandardOperator.calculate_stress(mixed_data, area=10.0)
    expected = pd.Series([10.0, -15.0, 20.0], name="force")  # Expected: no inversion as mean is not negative
    pd.testing.assert_series_equal(result, expected)


# Test 6: Invalid area (zero or negative)
@pytest.mark.parametrize("invalid_area", [0, -10])
def test_calculate_stress_invalid_area(typical_data, invalid_area):
    """Test that invalid area values raise an exception."""
    with pytest.raises(ValueError, match="Area must be a positive float or int."):
        BaseStandardOperator.calculate_stress(typical_data, area=invalid_area)


# Test 7: Invalid force_series type
def test_calculate_stress_invalid_force_series():
    """Test that passing an invalid force_series raises a TypeError."""
    with pytest.raises(TypeError, match="force_series must be a pandas Series."):
        BaseStandardOperator.calculate_stress([100, 150, 200], area=10.0)  # Passing a list instead of Series


# Test 8: Invalid conversion factor
@pytest.mark.parametrize("invalid_conversion", [0, -5])
def test_calculate_stress_invalid_conversion_factor(typical_data, invalid_conversion):
    """Test that invalid conversion factors raise an exception."""
    with pytest.raises(ValueError, match="Conversion factor must be a positive float or int."):
        BaseStandardOperator.calculate_stress(typical_data, area=10.0, conversion_factor=invalid_conversion)


# BaseStandardOperator test calculate_strain


# Fixture for typical displacement data
@pytest.fixture
def displacement_data() -> pd.Series:
    """Fixture for typical displacement values."""
    return pd.Series([0.05, 0.10, 0.15], name="displacement")  # Displacements in meters


@pytest.fixture
def large_negative_displacement() -> pd.Series:
    """Fixture for negative displacement values (compression)."""
    return pd.Series([-0.05, -0.10, -0.15], name="displacement")


@pytest.fixture
def mixed_displacement_data() -> pd.Series:
    """Fixture for mixed positive and negative displacement values."""
    return pd.Series([0.05, -0.10, 0.15], name="displacement")


# Test 1: Basic functionality
def test_calculate_strain_basic(displacement_data):
    """Test strain calculation for typical values."""
    result = BaseStandardOperator.calculate_strain(displacement_data, initial_length=1.0)
    expected = pd.Series([0.05, 0.10, 0.15], name="displacement")  # Strain = displacement / initial length
    pd.testing.assert_series_equal(result, expected)


# Test 2: With conversion factor
def test_calculate_strain_with_conversion(displacement_data):
    """Test strain calculation with a conversion factor."""
    result = BaseStandardOperator.calculate_strain(displacement_data, initial_length=1.0, conversion_factor=2.0)
    expected = pd.Series([0.10, 0.20, 0.30], name="displacement")  # Strain with conversion factor
    pd.testing.assert_series_equal(result, expected)


# Test 3: Inversion check for compression (negative strain values)
def test_calculate_strain_inversion(large_negative_displacement):
    """Test strain inversion for negative strain values."""
    result = BaseStandardOperator.calculate_strain(large_negative_displacement, initial_length=1.0)
    expected = pd.Series([0.05, 0.10, 0.15], name="displacement")  # Expected inverted strain for negative values
    pd.testing.assert_series_equal(result, expected)


# Test 4: No inversion when inversion_check is False
def test_calculate_strain_no_inversion(large_negative_displacement):
    """Test no inversion when inversion_check is False."""
    result = BaseStandardOperator.calculate_strain(
        large_negative_displacement, initial_length=1.0, inversion_check=False
    )
    expected = pd.Series([-0.05, -0.10, -0.15], name="displacement")  # No inversion expected
    pd.testing.assert_series_equal(result, expected)


# Test 5: Mixed displacement data with inversion check
def test_calculate_strain_mixed_data_inversion(mixed_displacement_data):
    """Test strain calculation for mixed positive and negative displacements."""
    result = BaseStandardOperator.calculate_strain(mixed_displacement_data, initial_length=1.0)
    expected = pd.Series([0.05, -0.10, 0.15], name="displacement")  # No inversion expected (mean is not negative)
    pd.testing.assert_series_equal(result, expected)


# Test 6: Invalid initial length (zero or negative)
@pytest.mark.parametrize("invalid_length", [0, -10])
def test_calculate_strain_invalid_initial_length(displacement_data, invalid_length):
    """Test that invalid initial length values raise an exception."""
    with pytest.raises(ValueError, match="Initial length must be a positive float or int."):
        BaseStandardOperator.calculate_strain(displacement_data, initial_length=invalid_length)


# Test 7: Invalid displacement_series type
def test_calculate_strain_invalid_displacement_series():
    """Test that passing an invalid displacement_series raises a TypeError."""
    with pytest.raises(TypeError, match="displacement_series must be a pandas Series."):
        BaseStandardOperator.calculate_strain(
            [0.05, 0.10, 0.15], initial_length=1.0
        )  # Passing a list instead of Series


# Test 8: Invalid conversion factor
@pytest.mark.parametrize("invalid_conversion", [0, -5])
def test_calculate_strain_invalid_conversion_factor(displacement_data, invalid_conversion):
    """Test that invalid conversion factors raise an exception."""
    with pytest.raises(ValueError, match="Conversion factor must be a positive float or int."):
        BaseStandardOperator.calculate_strain(
            displacement_data, initial_length=1.0, conversion_factor=invalid_conversion
        )


# BaseStandardOperator test interpolate_dataframes


# Fixture for typical input DataFrames
@pytest.fixture
def df_list() -> list[pd.DataFrame]:
    """Fixture for a list of DataFrames for interpolation."""
    df1 = pd.DataFrame({"time": [1, 2, 4, 5], "value": [10, 20, 40, 50]})
    df2 = pd.DataFrame({"time": [1, 3, 4, 6], "value": [15, 35, 45, 60]})
    return [df1, df2]


# Fixture for common axis
@pytest.fixture
def common_axis() -> pd.Series:
    """Fixture for common axis (shared index for interpolation)."""
    return pd.Series([1, 2, 3, 4, 5, 6], name="time")


# Test 1: Basic interpolation (linear)
def test_interpolate_dataframes_basic(df_list, common_axis):
    """Test basic linear interpolation on DataFrames."""
    result = BaseStandardOperator.interpolate_dataframes(
        df_list, interp_column="time", common_axis=common_axis, interpolation_method="linear"
    )

    # Expected DataFrame 1 after interpolation
    expected_df1 = pd.DataFrame({"time": [1, 2, 3, 4, 5, 6], "value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]}).set_index(
        "time"
    )

    # Expected DataFrame 2 after interpolation
    expected_df2 = pd.DataFrame({"time": [1, 2, 3, 4, 5, 6], "value": [15.0, 25.0, 35.0, 45.0, 52.5, 60.0]}).set_index(
        "time"
    )

    pd.testing.assert_frame_equal(result[0], expected_df1)
    pd.testing.assert_frame_equal(result[1], expected_df2)


# Test 2: Non-monotonic DataFrame (requires sorting)
def test_interpolate_dataframes_non_monotonic(df_list, common_axis):
    """Test interpolation with non-monotonic DataFrame."""
    # Create a non-monotonic DataFrame
    df_non_monotonic = pd.DataFrame({"time": [5, 4, 2, 1], "value": [50, 40, 20, 10]})

    # Add it to the list of DataFrames
    df_list.append(df_non_monotonic)

    result = BaseStandardOperator.interpolate_dataframes(
        df_list, interp_column="time", common_axis=common_axis, interpolation_method="linear"
    )

    # Expected DataFrame after sorting and interpolation
    expected_df_non_monotonic = pd.DataFrame(
        {"time": [1, 2, 3, 4, 5, 6], "value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]}
    ).set_index("time")

    pd.testing.assert_frame_equal(result[2], expected_df_non_monotonic)


# Test 3: Different interpolation methods (quadratic)
def test_interpolate_dataframes_quadratic(df_list, common_axis):
    """Test interpolation using quadratic method."""
    result = BaseStandardOperator.interpolate_dataframes(
        df_list, interp_column="time", common_axis=common_axis, interpolation_method="quadratic"
    )
    # Index 3 is not defined in the original DataFrame.
    df_1 = result[0]
    # It is interpolated using both linear and quadratic methods using the nearest points:
    # - [x0 = 2, y0 = 20]
    # - [x1 = 4, y1 = 40]
    #
    # Linear interpolation would give:
    # (y1 - y0) / (x1 - x0) = (40 - 20) / (4 - 2) = 10
    # So, interpolated y at x = 3 is:
    # y = 10 * (3 - 2) + 20 = 30.0
    #
    # For quadratic interpolation, we use three points to fit a quadratic curve:
    # - [x0 = 1, y0 = 10]
    # - [x1 = 2, y1 = 20]
    # - [x2 = 4, y2 = 40]
    #
    # The quadratic polynomial is of the form:
    # y = ax^2 + bx + c
    #
    # Using the three points, we can set up the following system of equations:
    # 1. For (x0 = 1, y0 = 10): a(1)^2 + b(1) + c = 10
    #    => a + b + c = 10
    # 2. For (x1 = 2, y1 = 20): a(2)^2 + b(2) + c = 20
    #    => 4a + 2b + c = 20
    # 3. For (x2 = 4, y2 = 40): a(4)^2 + b(4) + c = 40
    #    => 16a + 4b + c = 40
    #
    # Solving this system step by step:
    # 1. Subtract equation 1 from equation 2 to eliminate 'c':
    #    (4a + 2b + c) - (a + b + c) = 20 - 10
    #    => 3a + b = 10
    # 2. Subtract equation 2 from equation 3 to eliminate 'c':
    #    (16a + 4b + c) - (4a + 2b + c) = 40 - 20
    #    => 12a + 2b = 20 => 6a + b = 10
    # 3. Now we have the system:
    #    3a + b = 10
    #    6a + b = 10
    # 4. Subtract the first equation from the second to solve for 'a':
    #    (6a + b) - (3a + b) = 10 - 10
    #    => 3a = 0
    #    => a = 0
    # 5. Substitute 'a = 0' into the equation 3a + b = 10:
    #    3(0) + b = 10
    #    => b = 10
    # 6. Substitute 'a = 0' and 'b = 10' into the equation a + b + c = 10:
    #    0 + 10 + c = 10
    #    => c = 0
    #
    # Therefore, the quadratic polynomial is:
    # y = 10x
    #
    # Interpolating at x = 3:
    # y = 10 * 3 = 30.0
    #
    # So, both linear and quadratic interpolation will give the same result (30.0) at x = 3.

    assert df_1.loc[3, "value"] == 30.0


import numpy as np
import pandas as pd
import pytest

from standards.base.base_standard_operator import BaseStandardOperator

# Test _validate_positive_number


def test_validate_positive_number_valid():
    """Test that valid positive numbers pass without error."""
    BaseStandardOperator._validate_positive_number(10, "test_var")
    BaseStandardOperator._validate_positive_number(5.5, "test_var")


def test_validate_positive_number_invalid():
    """Test that invalid numbers raise the correct error."""
    with pytest.raises(ValueError, match="test_var must be a positive float or int."):
        BaseStandardOperator._validate_positive_number(0, "test_var")
    with pytest.raises(ValueError, match="test_var must be a positive float or int."):
        BaseStandardOperator._validate_positive_number(-5, "test_var")
    with pytest.raises(ValueError, match="test_var must be a positive float or int."):
        BaseStandardOperator._validate_positive_number("string", "test_var")


def test_validate_positive_number_with_parent_func_name():
    """Test error message when parent_func_name is provided."""
    with pytest.raises(ValueError, match="Func \\[test_func\\] | test_var must be a positive float or int."):
        BaseStandardOperator._validate_positive_number(-1, "test_var", parent_func_name="test_func")


# Test _validate_columns_exist


def test_validate_columns_exist_valid():
    """Test that DataFrames containing the required columns pass without error."""
    df1 = pd.DataFrame({"time": [1, 2], "value": [10, 20]})
    df2 = pd.DataFrame({"time": [1, 3], "value": [15, 30]})
    BaseStandardOperator._validate_columns_exist([df1, df2], ["time", "value"])


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
        BaseStandardOperator._validate_columns_exist([df1, df2], ["time", "value"])


def test_validate_columns_exist_no_name():
    """Test that unnamed DataFrames return their index in the error message."""
    df1 = pd.DataFrame({"time": [1, 2]})
    df2 = pd.DataFrame({"time": [1, 3], "value": [15, 30]})

    with pytest.raises(ValueError, match="DataFrame at index 0 is missing columns: value"):
        BaseStandardOperator._validate_columns_exist([df1, df2], ["time", "value"])

# Test get_dataframes_with_required_columns


def test_get_dataframes_with_required_columns():
    """Test that the function returns only DataFrames that have all the required columns."""
    df1 = pd.DataFrame({"time": [1, 2]})
    df2 = pd.DataFrame({"time": [1, 3], "value": [15, 30]})
    df3 = pd.DataFrame({"time": [1, 2], "value": [20, 40], "extra": [100, 200]})
    df1.name = "DF1"
    df2.name = "DF2"
    df3.name = "DF3"

    result = BaseStandardOperator._get_dataframes_with_required_columns([df1, df2, df3], ["time", "value"])

    assert result == [df2, df3]  # Only df2 and df3 have both 'time' and 'value' columns


# Test _generate_common_axis


def test_generate_common_axis_default_range():
    """Test that the common axis is created with the default start and end based on the data."""
    df1 = pd.DataFrame({"time": [1, 2, 3], "value": [10, 20, 30]})
    df2 = pd.DataFrame({"time": [2, 4, 6], "value": [15, 25, 35]})
    result = BaseStandardOperator._generate_common_axis([df1, df2], reference_column="time", axis_step=1.0)

    expected = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], name="time")
    pd.testing.assert_series_equal(result, expected)


def test_generate_common_axis_with_start_end():
    """Test that the common axis is created with a specified start and end."""
    df1 = pd.DataFrame({"time": [1, 2, 3], "value": [10, 20, 30]})
    df2 = pd.DataFrame({"time": [2, 4, 6], "value": [15, 25, 35]})
    result = BaseStandardOperator._generate_common_axis(
        [df1, df2], reference_column="time", axis_step=1.0, axis_start=0, axis_end=7
    )

    expected = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], name="time")
    pd.testing.assert_series_equal(result, expected)


def test_generate_common_axis_non_integer_step():
    """Test that the common axis is created with non-integer step size."""
    df1 = pd.DataFrame({"time": [1, 2, 3], "value": [10, 20, 30]})
    df2 = pd.DataFrame({"time": [2, 4, 6], "value": [15, 25, 35]})
    result = BaseStandardOperator._generate_common_axis([df1, df2], reference_column="time", axis_step=0.5)

    expected = pd.Series([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0], name="time")
    pd.testing.assert_series_equal(result, expected)


# BaseStandardOperator test average_dataframes
# Fixture for a list of identical DataFrames (no interpolation needed)


@pytest.fixture
def df_list_same() -> list[pd.DataFrame]:
    df1 = pd.DataFrame(
        {"interp_column": np.arange(0, 10, 1), "col1": np.arange(0, 10, 1), "col2": np.arange(10, 20, 1)}
    )
    df2 = pd.DataFrame(
        {"interp_column": np.arange(0, 10, 1), "col1": np.arange(0, 10, 1), "col2": np.arange(10, 20, 1)}
    )
    return [df1, df2]


# Fixture for DataFrames with different interp_column values - X (interpolation needed)
@pytest.fixture
def df_list_different() -> list[pd.DataFrame]:
    df1 = pd.DataFrame(
        {"interp_column": np.arange(0, 10, 1), "col1": np.arange(0, 10, 1), "col2": np.arange(10, 20, 1)}
    )
    df2 = pd.DataFrame(
        {"interp_column": np.arange(0, 20, 2), "col1": np.arange(0, 10, 1), "col2": np.arange(10, 20, 1)}
    )
    return [df1, df2]


# Test 1: Basic functionality (no interpolation needed)
def test_average_dataframes_no_interpolation(df_list_same):
    result = BaseStandardOperator.average_dataframes(
        df_list=df_list_same, avg_columns="col1", interp_column="interp_column", step_size=1.0
    )

    expected = pd.DataFrame({"interp_column": np.arange(0, 10, 1), "avg_col1": np.arange(0, 10, 1)})
    # set the types to be the result and expected to be the same
    expected = expected.astype(result.dtypes)
    pd.testing.assert_frame_equal(result, expected)


# Test 2: Interpolation needed (different interp_column)
def test_average_dataframes_with_interpolation(df_list_different):
    # df_list_different contains two DataFrames with different interp_column values.
    # df1:                              # df2:
    #    interp_column  col1  col2      #    interp_column  col1  col2
    # 0              0     0    10      # 0              0     0    10
    # 1              1     1    11      # 1              2     1    11
    # 2              2     2    12      # 2              4     2    12
    # 3              3     3    13      # 3              6     3    13
    # 4              4     4    14      # 4              8     4    14
    # 5              5     5    15      # 5             10     5    15
    # 6              6     6    16      # 6             12     6    16
    # 7              7     7    17      # 7             14     7    17
    # 8              8     8    18      # 8             16     8    18
    # 9              9     9    19      # 9             18     9    19

    # Common axis will be: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18].

    # The interpolatated values
    # df1:                              # df2:
    #    interp_column  col1  col2      #    interp_column  col1  col2
    # 0             0     0    10       # 0              0     0    10
    # 1             1     1    11       # 1              1     0.5  10.5
    # 2             2     2    12       # 2              2     1    11
    # 3             3     3    13       # 3              3     1.5  11.5
    # 4             4     4    14       # 4              4     2    12
    # 5             5     5    15       # 5              5     2.5  12.5
    # 6             6     6    16       # 6              6     3    13
    # 7             7     7    17       # 7              7     3.5  13.5
    # 8             8     8    18       # 8              8     4    14
    # 9             9     9    19       # 9              9     4.5  14.5
    # 10           10    10    20       # 10            10     5    15
    # 11           11    11    21       # 11            11     5.5  15.5
    # 12           12    12    22       # 12            12     6    16
    # 13           13    13    23       # 13            13     6.5  16.5
    # 14           14    14    24       # 14            14     7    17
    # 15           15    15    25       # 15            15     7.5  17.5
    # 16           16    16    26       # 16            16     8    18
    # 17           17    17    27       # 17            17     8.5  18.5
    # 18           18    18    28       # 18            18     9    19

    # The average values will be:
    #    interp_column      avg_col1                        avg_col2
    # 0              0      (0 + 0) / 2 = 0                 (10 + 10) / 2 = 10
    # 1              1      (1 + 0.5) / 2 = 0.75            (11 + 10.5) / 2 = 10.75
    # 2              2      (2 + 1) / 2 = 1.5               (12 + 11) / 2 = 11.5
    # 3              3      (3 + 1.5) / 2 = 2.25            (13 + 11.5) / 2 = 12.25
    # 4              4      (4 + 2) / 2 = 3                 (14 + 12) / 2 = 13
    # 5              5      (5 + 2.5) / 2 = 3.75            (15 + 12.5) / 2 = 13.75
    # 6              6      (6 + 3) / 2 = 4.5               (16 + 13) / 2 = 14.5
    # 7              7      (7 + 3.5) / 2 = 5.25            (17 + 13.5) / 2 = 15.25
    # 8              8      (8 + 4) / 2 = 6                 (18 + 14) / 2 = 16
    # 9              9      (9 + 4.5) / 2 = 6.75            (19 + 14.5) / 2 = 16.75
    # 10            10     (10 + 5) / 2 = 7.5               (20 + 15) / 2 = 17.5
    # 11            11     (11 + 5.5) / 2 = 8.25            (21 + 15.5) / 2 = 18.25
    # 12            12     (12 + 6) / 2 = 9                 (22 + 16) / 2 = 19
    # 13            13     (13 + 6.5) / 2 = 9.75            (23 + 16.5) / 2 = 19.75
    # 14            14     (14 + 7) / 2 = 10.5              (24 + 17) / 2 = 20.5
    # 15            15     (15 + 7.5) / 2 = 11.25           (25 + 17.5) / 2 = 21.25
    # 16            16     (16 + 8) / 2 = 12                (26 + 18) / 2 = 22
    # 17            17     (17 + 8.5) / 2 = 12.75           (27 + 18.5) / 2 = 22.75
    # 18            18     (18 + 9) / 2 = 13.5              (28 + 19) / 2 = 23.5

    result = BaseStandardOperator.average_dataframes(
        df_list=df_list_different, avg_columns="col1", interp_column="interp_column", step_size=1.0
    )

    expected_interp_column = np.arange(0, 19, 1)
    expected_avg_col1 = pd.Series(
        [0.0, 0.75, 1.5, 2.25, 3.0, 3.75, 4.5, 5.25, 6.0, 6.75, 7.5, 8.25, 9.0, 9.75, 10.5, 11.25, 12.0, 12.75, 13.5],
    )
    expected_avg_col2 = pd.Series(
        [
            10.0,
            10.75,
            11.5,
            12.25,
            13.0,
            13.75,
            14.5,
            15.25,
            16.0,
            16.75,
            17.5,
            18.25,
            19.0,
            19.75,
            20.5,
            21.25,
            22.0,
            22.75,
            23.5,
        ],
    )
    expected = pd.DataFrame(
        {
            "interp_column": expected_interp_column,
            "avg_col1": expected_avg_col1,
        },
        dtype="float64",
    )

    pd.testing.assert_frame_equal(result, expected)


# Test 3: Invalid step size
def test_average_dataframes_invalid_step_size(df_list_same):
    with pytest.raises(ValueError, match="Func [average_dataframes] | Step size must be a positive float or int."):
        BaseStandardOperator.average_dataframes(
            df_list=df_list_same, avg_columns="col1", interp_column="interp_column", step_size=0
        )


# Test 4: Invalid df_list input (not a list of DataFrames)
def test_average_dataframes_invalid_df_list():
    with pytest.raises(TypeError, match="df_list must be a list of pandas DataFrames."):
        BaseStandardOperator.average_dataframes(
            df_list="not_a_list", avg_columns="col1", interp_column="interp_column", step_size=1.0
        )
