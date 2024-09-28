import numpy as np
import pandas as pd
import pytest
from uncertainties import ufloat

from standards.base.properties_calculators.base_standard_operator import BaseStandardOperator

# Round-off error comes from the approximation of real numbers. eg. 1/3 = 0.3333333333333333 (infinite decimal places)
# the acuracy is dependent on the anount of memory (bits) allocated to store the number.

# float64 (double precision floating-point) has:
# Precision: Approximately 15–17 significant decimal digits.
# Machine epsilon (eps): 2.220446049250313e-16 (approx. 1e-16) - The smallest difference between two representable numbers.

# Relative tolerance (rtol) should be set relative to the scale of the numbers being compared.
# For float64 precision, an rtol of around 1e-7 to 1e-9 is typically sufficient for most engineering calculations.
RELATIVE_TOLERANCE_G = 1e-9

# Absolute tolerance (atol) is useful when comparing numbers near zero, where relative tolerance alone might not be sufficient.
# It should be set to a small value, such as 1e-8 or 1e-10, to account for very small absolute differences.
ABSOLUTE_TOLERANCE_G = 1e-10  # 10 decimal places

# BaseStandardOperator test: Cross-sectional area calculation
# Testing this function in detail with uncertainty handling due to the additional complexity
# introduced by uncertainty propagation. Normally, the calculation of the area (length * width)
# would not be thoroughly tested due to its simplicity. However, uncertainties require
# validation to ensure no unintended side effects.

# Truncation error is t
# eg.1 taylor series expansion of sin(x) = x - x^3/3! + x^5/5! - x^7/7! + ...
# if we truncate the series at x^3 (term), we have an  (truncation) error of x^5/5! + x^7/7! + ...
# eg.2 derivative of f(x) = (f(x+h) - f(x))/h as h -> 0, the error is O(h) (order of h)
# the error is proportional to step size h, thus the (truncation) error is dependent on the step size.


# BaseStandardOperator test calculate_cross_sectional_area

# Test 1: Basic area calculation
def test_calculate_cross_sectional_area_basic():
    result = BaseStandardOperator.calculate_cross_sectional_area(length=10.0, width=5.0)
    assert result.value == 50.0
    assert result.uncertainty == 0.0  # No uncertainty provided


# Test 2: Area calculation with conversion factor
def test_calculate_cross_sectional_area_with_conversion():
    result = BaseStandardOperator.calculate_cross_sectional_area(length=10.0, width=5.0, conversion_factor=2.0)
    assert result.value == 100.0  # Area * conversion factor
    assert result.uncertainty == 0.0


# Test 3: Area calculation with scalar uncertainties
def test_calculate_cross_sectional_area_with_uncertainty():
    length = 10.0
    width = 5.0
    length_uncertainty = 0.1
    width_uncertainty = 0.2

    # Calculate expected area and uncertainty manually
    # Area = length * width
    # Uncertainty = sqrt((dA/dl * uncertainty_length)^2 + (dA/dw * uncertainty_width)^2)
    expected_value = length * width  # 50.0
    relative_uncertainty_length = length_uncertainty / length  # 0.01
    relative_uncertainty_width = width_uncertainty / width  # 0.04
    combined_relative_uncertainty = np.sqrt(relative_uncertainty_length**2 + relative_uncertainty_width**2)  # 0.04123
    expected_uncertainty = expected_value * combined_relative_uncertainty  # 50.0 * 0.04123 = 2.0615

    # Call function and compare
    result = BaseStandardOperator.calculate_cross_sectional_area(
        length=length, width=width, length_uncertainty=length_uncertainty, width_uncertainty=width_uncertainty
    )
    assert result.value == expected_value  # Check nominal value
    assert result.uncertainty == pytest.approx(expected_uncertainty, rel=1e-5)


# Test 4: Area calculation with percentage uncertainties
def test_calculate_cross_sectional_area_with_percentage_uncertainty():
    length = 10.0
    width = 5.0
    length_uncertainty = "5%"  # 0.05 as a relative uncertainty
    width_uncertainty = "10%"  # 0.10 as a relative uncertainty

    # Calculate expected area and uncertainty manually
    expected_value = length * width  # 50.0
    relative_uncertainty_length = 0.05  # 5% uncertainty in length
    relative_uncertainty_width = 0.10  # 10% uncertainty in width
    combined_relative_uncertainty = np.sqrt(relative_uncertainty_length**2 + relative_uncertainty_width**2)  # 0.1118
    expected_uncertainty = expected_value * combined_relative_uncertainty  # 50.0 * 0.1118 = 5.59

    # Call function and compare
    result = BaseStandardOperator.calculate_cross_sectional_area(
        length=length, width=width, length_uncertainty=length_uncertainty, width_uncertainty=width_uncertainty
    )
    assert result.value == expected_value  # Check nominal value
    assert result.uncertainty == pytest.approx(expected_uncertainty, rel=RELATIVE_TOLERANCE_G)  # Check uncertainty


# Test 5: Area calculation with no uncertainties
def test_calculate_cross_sectional_area_no_uncertainty():
    result = BaseStandardOperator.calculate_cross_sectional_area(length=10.0, width=5.0)
    assert result.value == 50.0
    assert result.uncertainty == 0.0  # No uncertainties provided


# Test 6: Invalid length or width values (zero or negative)
@pytest.mark.parametrize("invalid_value", [0, -10])
def test_calculate_cross_sectional_area_invalid_length_width(invalid_value):
    with pytest.raises(ValueError, match="Length must be a positive float or int"):
        BaseStandardOperator.calculate_cross_sectional_area(length=invalid_value, width=5.0)
    with pytest.raises(ValueError, match="Width must be a positive float or int"):
        BaseStandardOperator.calculate_cross_sectional_area(length=10.0, width=invalid_value)


# Test 7: Invalid uncertainty values
@pytest.mark.parametrize("invalid_uncertainty", [-0.1, "invalid", -5.0])
def test_calculate_cross_sectional_area_invalid_uncertainty(invalid_uncertainty):
    # Expect calculate_cross_sectional_area: Invalid uncertainty for Length. Must be a positive float or a percentage string. Received: -0.1
    with pytest.raises(
        ValueError, match=r".*Invalid uncertainty for Length. Must be a positive float or a percentage string.*"
    ):
        BaseStandardOperator.calculate_cross_sectional_area(
            length=10.0, width=5.0, length_uncertainty=invalid_uncertainty
        )


# Test 8: One-dimensional uncertainty only
def test_calculate_cross_sectional_area_one_dimension_uncertainty():
    result = BaseStandardOperator.calculate_cross_sectional_area(length=10.0, width=5.0, length_uncertainty=0.1)
    expected_area = ufloat(10.0, 0.1) * 5.0  # Uncertainty in length only
    assert result.value == expected_area.nominal_value
    assert result.uncertainty == pytest.approx(expected_area.std_dev, rel=RELATIVE_TOLERANCE_G)


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
    result, uncertainty = BaseStandardOperator.calculate_stress(typical_data, area=10.0)
    expected = pd.Series(
        [10.0, 15.0, 20.0], name="stress"
    )  # Expected stress = force / area  - will be a float because of area
    pd.testing.assert_series_equal(result, expected)
    # Uncertainty should be 0 as no uncertainty is provided
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="stress uncertainty", dtype=int))


# Test 2: With conversion factor
def test_calculate_stress_with_conversion(typical_data):
    """Test stress calculation with a conversion factor."""
    result, uncertainty = BaseStandardOperator.calculate_stress(typical_data, area=10.0, conversion_factor=2.0)
    expected = pd.Series([20.0, 30.0, 40.0], name="stress")  # Expected stress with conversion factor
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="stress uncertainty", dtype=int))


# Test 3: Inversion check for compression (negative stress values)
def test_calculate_stress_inversion(large_negative_data):
    """Test stress inversion for negative stress values."""
    result, uncertainty = BaseStandardOperator.calculate_stress(large_negative_data, area=10.0)
    expected = pd.Series([10.0, 15.0, 20.0], name="stress")  # Expected inverted stress for negative values
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="stress uncertainty", dtype=int))


# Test 4: No inversion when inversion_check is False
def test_calculate_stress_no_inversion(large_negative_data):
    """Test no inversion when inversion_check is False."""
    result, uncertainty = BaseStandardOperator.calculate_stress(large_negative_data, area=10.0, inversion_check=False)
    expected = pd.Series([-10.0, -15.0, -20.0], name="stress")  # No inversion expected
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="stress uncertainty", dtype=int))

# Test 5: Mixed forces with inversion check
def test_calculate_stress_mixed_data_inversion(mixed_data):
    """Test stress calculation for mixed positive and negative forces."""
    result, uncertainty = BaseStandardOperator.calculate_stress(mixed_data, area=10.0)
    expected = pd.Series([10.0, -15.0, 20.0], name="stress")  # Expected: no inversion as mean is not negative
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="stress uncertainty", dtype=int))


# Test 6: Invalid area (zero or negative)
@pytest.mark.parametrize("invalid_area", [0, -10])
def test_calculate_stress_invalid_area(typical_data, invalid_area):
    """Test that invalid area values raise an exception."""
    with pytest.raises(ValueError, match="Area must be a positive float or int."):
        BaseStandardOperator.calculate_stress(typical_data, area=invalid_area)


# Test 7: Invalid force_series type
def test_calculate_stress_invalid_force_series():
    """Test that passing an invalid force_series raises a TypeError."""
    with pytest.raises(TypeError, match=r".*force_series must be.*"):
        # Expect: force_series must be of type(s) Series in function [calculate_stress]. Received: list
        BaseStandardOperator.calculate_stress([100, 150, 200], area=10.0)  # Passing a list instead of Series


# Test 8: Invalid conversion factor
@pytest.mark.parametrize("invalid_conversion", [0, -5])
def test_calculate_stress_invalid_conversion_factor(typical_data, invalid_conversion):
    """Test that invalid conversion factors raise an exception."""
    # Expect: 'Conversion Factor must be a positive float or int in function [calculate_stress]. Received: 0'
    with pytest.raises(ValueError, match="Conversion Factor must be a positive float or int"):
        BaseStandardOperator.calculate_stress(typical_data, area=10.0, conversion_factor=invalid_conversion)

# Test 9: Basic uncertainty calculation with scalar uncertainties
def test_calculate_stress_with_scalar_uncertainty():
    force_series = pd.Series([100, 150, 200], name="force")
    area = 10.0
    force_uncertainty = 5.0  # 5 N uncertainty for all forces
    area_uncertainty = 0.1  # 0.1 cm^2 uncertainty for area

    # Step 1: Calculate expected stress
    # Nominal stress = force / area, basic calculation.
    # Expected stress: [10.0, 15.0, 20.0]
    expected_stress = force_series / area
    # Rename Force to Stress (As series / scalar give Series with the same name 'force')
    expected_stress = expected_stress.rename("stress")

    # Step 2: Calculate relative uncertainty for force
    # Relative uncertainty for force is calculated as sigma(force) / force.
    relative_uncertainty_force = force_uncertainty / force_series
    # Rename Force to Force Uncertainty As series / scalar give Series with the same name 'force')
    relative_uncertainty_force = relative_uncertainty_force.rename("force uncertainty")
    # Expected: [0.05, 0.03333, 0.025]
    expected_relative_uncertainty_force = pd.Series([0.05, 0.03333333333333333, 0.025], name="force uncertainty")

    # Step 3: Calculate relative uncertainty for area (scalar)
    # Relative uncertainty for area, which is a constant here. A small change in area (e.g., 0.1 cm^2) can have significant
    # effects on stress calculations, especially for high-force scenarios.
    relative_uncertainty_area = area_uncertainty / area  # Expected: 0.01
    assert relative_uncertainty_area == 0.01

    # Step 4: Combine relative uncertainties (element-wise)
    # The combined relative uncertainty considers both force and area uncertainties.
    # This calculation is crucial for understanding the overall uncertainty in stress due to input uncertainties.
    combined_relative_uncertainty = np.sqrt(relative_uncertainty_force**2 + relative_uncertainty_area**2)
    # Rename Force to Stress (As series *  scalar give the same name 'force uncertainty')
    combined_relative_uncertainty = combined_relative_uncertainty.rename("force uncertainty")
    expected_combined_relative_uncertainty = pd.Series(
        np.sqrt([0.05**2 + 0.01**2, 0.03333333333333333**2 + 0.01**2, 0.025**2 + 0.01**2]), name="force uncertainty"
    )
    pd.testing.assert_series_equal(
        combined_relative_uncertainty,
        expected_combined_relative_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )

    # Step 5: Calculate absolute uncertainty in stress
    # Absolute uncertainty in stress is calculated as stress * combined_relative_uncertainty.
    expected_stress_uncertainty = expected_stress * combined_relative_uncertainty
    # Rename None to Stress Uncertainty (As series * series give a Series with the name = None)
    expected_stress_uncertainty = expected_stress_uncertainty.rename("stress uncertainty")
    expected_absolute_stress_uncertainty = pd.Series(
        [
            10.0 * np.sqrt(0.05**2 + 0.01**2),
            15.0 * np.sqrt(0.03333333333333333**2 + 0.01**2),
            20.0 * np.sqrt(0.025**2 + 0.01**2),
        ],
        name="stress uncertainty",
    )

    # Check all intermediate calculations
    # Check Nominal Value for Stress
    pd.testing.assert_series_equal(expected_stress, pd.Series([10.0, 15.0, 20.0], name="stress"))
    # Check Relative Uncertainty for Force
    pd.testing.assert_series_equal(
        relative_uncertainty_force,
        expected_relative_uncertainty_force,
        rtol=RELATIVE_TOLERANCE_G,  # Choosing 1e-9 to ensure high precision, reflecting engineering safety standards.
        atol=ABSOLUTE_TOLERANCE_G,  # Absolute tolerance is low as we are working with relative uncertainties.
    )
    # Check combined relative uncertainty of area and force with error propagation

    pd.testing.assert_series_equal(
        expected_stress_uncertainty,
        expected_absolute_stress_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )

    # Step 6: Call the function and compare all outputs
    result = BaseStandardOperator.calculate_stress(
        force_series=force_series, area=area, force_uncertainty=force_uncertainty, area_uncertainty=area_uncertainty
    )

    # Check final calculated stress values and uncertainties
    pd.testing.assert_series_equal(result.value, expected_stress)
    pd.testing.assert_series_equal(
        result.uncertainty,
        expected_stress_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )


# Test 10:  Stress Calculation with Scalar Uncertainties


def test_calculate_stress_with_percentage_uncertainty():
    force_series = pd.Series([100, 150, 200], name="force")
    area = 10.0
    force_uncertainty = "5%"  # 5% uncertainty in force
    area_uncertainty = "2%"  # 2% uncertainty in area

    # Nominal stress = force / area
    expected_stress = force_series / area  # Expected stress: [10.0, 15.0, 20.0]
    expected_stress = expected_stress.rename(
        "stress"
    )  # Raneme Force to Stress (As series *  scalar give the same name)

    # 5% uncertainty means relative uncertainty is 0.05 for all forces
    relative_uncertainty_force = 0.05
    expected_relative_uncertainty_force = pd.Series([relative_uncertainty_force] * 3, name="force uncertainty")

    relative_uncertainty_area = 0.02  # 2% uncertainty in area

    # Combined relative uncertainty considers both force and area uncertainties
    combined_relative_uncertainty = np.sqrt(relative_uncertainty_force**2 + relative_uncertainty_area**2)
    expected_combined_relative_uncertainty = pd.Series([combined_relative_uncertainty] * 3, name="stress uncertainty")

    # Absolute uncertainty in stress = stress * combined relative uncertainty
    expected_stress_uncertainty = expected_stress * combined_relative_uncertainty
    expected_stress_uncertainty = expected_stress_uncertainty.rename(
        "stress uncertainty"
    )  # Rename Stress to Stress Uncertainty (As series *  scalar give the same name)
    expected_absolute_stress_uncertainty = pd.Series(
        [
            10.0 * combined_relative_uncertainty,
            15.0 * combined_relative_uncertainty,
            20.0 * combined_relative_uncertainty,
        ],
        name="stress uncertainty",
    )

    result = BaseStandardOperator.calculate_stress(
        force_series=force_series, area=area, force_uncertainty=force_uncertainty, area_uncertainty=area_uncertainty
    )

    # Check final calculated stress values and uncertainties
    # Check Nominal Value
    pd.testing.assert_series_equal(expected_stress, pd.Series([10.0, 15.0, 20.0], name="stress"))
    # Check Relative Uncertainty for Force
    pd.testing.assert_series_equal(
        pd.Series([relative_uncertainty_force] * 3, name="force uncertainty"),
        expected_relative_uncertainty_force,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )
    # Check combined relative uncertainty of area and force with error propagation
    pd.testing.assert_series_equal(
        pd.Series([combined_relative_uncertainty] * 3, name="stress uncertainty"),
        expected_combined_relative_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )
    # Check absolute uncertainty in stress
    pd.testing.assert_series_equal(
        expected_stress_uncertainty,
        expected_absolute_stress_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )
    # Check BaseStandardOperator.calculate_stress output is similar to manual calculation
    # stress check
    pd.testing.assert_series_equal(result.value, expected_stress)
    # uncertantiy check
    pd.testing.assert_series_equal(
        result.uncertainty,
        expected_stress_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )


# Test 11:   Stress Calculation with Series Uncertainties


def test_calculate_stress_with_series_uncertainty():
    force_series = pd.Series([100, 150, 200], name="force")
    area = 10.0
    force_uncertainty = pd.Series([5, 7, 10], name="force uncertainty")  # Different uncertainty for each force
    area_uncertainty = 0.1  # Scalar uncertainty for area

    # Step 1: Calculate expected stress
    # Expected stress: [10.0, 15.0, 20.0]
    expected_stress = force_series / area
    # Rename None to Stress (As series / scalar give None)
    expected_stress = expected_stress.rename("stress")

    # Step 2: Calculate relative uncertainty for force
    # Expected: [0.05, 0.04667, 0.05]
    relative_uncertainty_force = force_uncertainty / force_series
    # Rename Nonw to Force Uncertainty (As series / series give None)
    relative_uncertainty_force = relative_uncertainty_force.rename("force uncertainty")
    expected_relative_uncertainty_force = pd.Series([0.05, 0.04666666666666667, 0.05], name="force uncertainty")

    # Step 3: Calculate relative uncertainty for area (scalar)
    relative_uncertainty_area = area_uncertainty / area  # Expected: 0.01
    assert relative_uncertainty_area == 0.01

    # Step 4: Combine relative uncertainties (element-wise)
    combined_relative_uncertainty = np.sqrt(relative_uncertainty_force**2 + relative_uncertainty_area**2)
    # Rename Force to Stress (As series *  scalar give the same name)
    combined_relative_uncertainty = combined_relative_uncertainty.rename("stress uncertainty")

    expected_combined_relative_uncertainty = pd.Series(
        np.sqrt([0.05**2 + 0.01**2, 0.04666666666666667**2 + 0.01**2, 0.05**2 + 0.01**2]), name="stress uncertainty"
    )

    # Step 5: Calculate absolute uncertainty in stress
    expected_stress_uncertainty = expected_stress * combined_relative_uncertainty
    # Rename None to Stress Uncertainty As series * series give None
    expected_stress_uncertainty = expected_stress_uncertainty.rename("stress uncertainty")
    expected_absolute_stress_uncertainty = pd.Series(
        [
            10.0 * np.sqrt(0.05**2 + 0.01**2),
            15.0 * np.sqrt(0.04666666666666667**2 + 0.01**2),
            20.0 * np.sqrt(0.05**2 + 0.01**2),
        ],
        name="stress uncertainty",
    )

    # Step 6: Call the function and compare all outputs
    result = BaseStandardOperator.calculate_stress(
        force_series=force_series, area=area, force_uncertainty=force_uncertainty, area_uncertainty=area_uncertainty
    )

    # Check final calculated stress values and uncertainties
    # Check Nominal Value
    pd.testing.assert_series_equal(expected_stress, pd.Series([10.0, 15.0, 20.0], name="stress"))
    # Check Relative Uncertainty for Force
    pd.testing.assert_series_equal(
        relative_uncertainty_force,
        expected_relative_uncertainty_force,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )
    # Check combined relative uncertainty of area and force with error propagation
    pd.testing.assert_series_equal(
        combined_relative_uncertainty,
        expected_combined_relative_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )
    # Check absolute uncertainty in stress
    pd.testing.assert_series_equal(
        expected_stress_uncertainty,
        expected_absolute_stress_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )
    # Check BaseStandardOperator.calculate_stress output is similar to manual calculation
    # stress check
    pd.testing.assert_series_equal(result.value, expected_stress)
    # uncertantiy check
    pd.testing.assert_series_equal(
        result.uncertainty,
        expected_stress_uncertainty,
        rtol=RELATIVE_TOLERANCE_G,
        atol=ABSOLUTE_TOLERANCE_G,
    )


# Test 12:  Zero and Negative Uncertainties Handling
@pytest.mark.parametrize("invalid_uncertainty", [0, -1])
def test_calculate_stress_invalid_uncertainty(invalid_uncertainty):
    force_series = pd.Series([100, 150, 200], name="force")
    area = 10.0

    # Test invalid force uncertainty
    # Expect: calculate_stress: Invalid absolute uncertainty for Force must be a positive value. Received: 0
    with pytest.raises(ValueError, match=".*Invalid absolute uncertainty for Force. Must be a positive value.*"):
        BaseStandardOperator.calculate_stress(
            force_series=force_series, area=area, force_uncertainty=invalid_uncertainty
        )

    # Test invalid area uncertainty
    with pytest.raises(
        ValueError, match=".*Invalid uncertainty for Area. Must be a positive float or a percentage string.*"
    ):
        BaseStandardOperator.calculate_stress(
            force_series=force_series, area=area, area_uncertainty=invalid_uncertainty
        )


# Test 13: Empty Force Series Check
def test_calculate_stress_empty_force_series():
    force_series = pd.Series([], dtype=float, name="force")  # Empty force series
    area = 10.0

    # Expecting ValueError due to empty force_series

    with pytest.raises(ValueError, match=".*Force Series must contain at least one force value.*"):
        BaseStandardOperator.calculate_stress(force_series=force_series, area=area)


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
    result, uncertainty = BaseStandardOperator.calculate_strain(displacement_data, initial_length=1.0)
    # Strain = displacement / initial length
    expected = pd.Series([0.05, 0.10, 0.15], name="strain")  # Expected strain values
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="strain uncertainty", dtype=int))


# Test 2: With conversion factor
def test_calculate_strain_with_conversion(displacement_data):
    """Test strain calculation with a conversion factor."""
    result, uncertainty = BaseStandardOperator.calculate_strain(
        displacement_data, initial_length=1.0, conversion_factor=2.0
    )
    # Strain with conversion factor
    expected = pd.Series([0.10, 0.20, 0.30], name="strain")
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="strain uncertainty", dtype=int))


# Test 3: Inversion check for compression (negative strain values)
def test_calculate_strain_inversion(large_negative_displacement):
    """Test strain inversion for negative strain values."""
    result, uncertainty = BaseStandardOperator.calculate_strain(large_negative_displacement, initial_length=1.0)
    expected = pd.Series([0.05, 0.10, 0.15], name="strain")  # Expected inverted strain for negative values
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="strain uncertainty", dtype=int))


# Test 4: No inversion when inversion_check is False
def test_calculate_strain_no_inversion(large_negative_displacement):
    """Test no inversion when inversion_check is False."""
    result, uncertainty = BaseStandardOperator.calculate_strain(
        large_negative_displacement, initial_length=1.0, inversion_check=False
    )
    expected = pd.Series([-0.05, -0.10, -0.15], name="strain")  # No inversion expected
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="strain uncertainty", dtype=int))


# Test 5: Mixed displacement data with inversion check
def test_calculate_strain_mixed_data_inversion(mixed_displacement_data):
    """Test strain calculation for mixed positive and negative displacements."""
    result, uncertainty = BaseStandardOperator.calculate_strain(mixed_displacement_data, initial_length=1.0)
    expected = pd.Series([0.05, -0.10, 0.15], name="strain")  # No inversion expected (mean is not negative)
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(uncertainty, pd.Series([0.0], name="strain uncertainty", dtype=int))


# Test 6: Invalid initial length (zero or negative)
@pytest.mark.parametrize("invalid_length", [0, -10])
def test_calculate_strain_invalid_initial_length(displacement_data, invalid_length):
    """Test that invalid initial length values raise an exception."""
    with pytest.raises(ValueError, match=r".*Initial Length must be a positive float or int.*"):
        BaseStandardOperator.calculate_strain(displacement_data, initial_length=invalid_length)


# Test 7: Invalid displacement_series type
def test_calculate_strain_invalid_displacement_series():
    """Test that passing an invalid displacement_series raises a TypeError."""
    with pytest.raises(TypeError, match=r".*displacement_series must be.*"):
        BaseStandardOperator.calculate_strain(
            [0.05, 0.10, 0.15], initial_length=1.0
        )  # Passing a list instead of Series


# Test 8: Invalid conversion factor
@pytest.mark.parametrize("invalid_conversion", [0, -5])
def test_calculate_strain_invalid_conversion_factor(displacement_data, invalid_conversion):
    """Test that invalid conversion factors raise an exception."""
    with pytest.raises(ValueError, match=r".*Conversion Factor must be a positive float or int.*"):
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
    # Expect: Step size must be a positive float or int in function [average_dataframes]. Received: 0
    with pytest.raises(ValueError, match=r".*Step size must be a positive float or int.*"):
        BaseStandardOperator.average_dataframes(
            df_list=df_list_same, avg_columns="col1", interp_column="interp_column", step_size=0
        )


# Test 4: Invalid df_list input (not a list of DataFrames)
def test_average_dataframes_invalid_df_list():
    # Expect: df_list must be of type(s) list in function [average_dataframes]. Received: str
    with pytest.raises(TypeError, match=r".*df_list must be of type\(s\) list.*"):
        BaseStandardOperator.average_dataframes(
            df_list="not_a_list", avg_columns="col1", interp_column="interp_column", step_size=1.0
        )

# BaseStandardOperator test find_intersections

# --- Fixtures ---


@pytest.fixture
def linear_quadratic_data():
    x = np.linspace(-5, 5, 100)
    # data frequencis is 10/100 = 0.1 | (Range/# pts)
    # Range = 10, [end (5) - start (-5) ]
    # data feq 10 [Hz] there is a point every 0.1 | (1/0.1)
    y1 = 2 * x + 1  # Linear: y = 2x + 1
    y2 = (x**2) - 4  # Quadratic: y = x^2 - 4
    # Analytical intersections
    expected_intersections = [(-1.44949, -1.89898), (3.44949, 7.89898)]
    return (x, y1), (x, y2), expected_intersections


@pytest.fixture
def sin_cos_data():
    x = np.linspace(0, 10, 100)
    # data frequencis is 10/100 = 0.1, 1/0.1 = 10 Hx
    y1 = np.sin(x)  # Curve 1: sin(x)
    y2 = np.cos(x)  # Curve 2: cos(x)
    # Expected intersections near pi/4, 5pi/4, etc. | 3 intersections from 0 to 10
    # 3 intersections, low data frequency, non-linear (close to linear at small angles)
    first_point = (np.pi / 4, np.sin(np.pi / 4))
    second_point = (5 * np.pi / 4, np.sin(5 * np.pi / 4))
    third_point = (9 * np.pi / 4, np.sin(9 * np.pi / 4))
    expected_intersections = [first_point, second_point, third_point]
    return (x, y1), (x, y2), expected_intersections


@pytest.fixture
def exponential_logarithmic_data():
    # Start from 1 to avoid log(0)
    x = np.linspace(1, 5, 100)
    # data frequencis is 4/100 = 0.04, 1/0.04 = 25 Hz
    # no intersections, non-linear, high data frequency
    y1 = np.exp(x)  # Exponential: y = e^x
    y2 = np.log(x)  # Logarithmic: y = ln(x)
    # Expected intersections are not defined explicitly; we will use approximate matches.
    return (x, y1), (x, y2), None


@pytest.fixture
def inverse_polynomial_data():
    x = np.linspace(0.1, 3, 100)  # Start from 0.1 to avoid division by zero
    # Data frequencis is 3/100 = 0.03, 1/0.03 = 33.33 Hz
    # 1 intersection, High data frequency, Very non-linear
    y1 = 1 / x  # Inverse: y = 1/x
    y2 = (x**3) - x  # Polynomial: y = x^3 - x
    expected_intersections = [(1.27202, 0.78615)]
    return (x, y1), (x, y2), expected_intersections


# Test 1: Basic intersection detection with linear interpolation
def test_find_intersections_basic_linear(sin_cos_data, linear_quadratic_data, inverse_polynomial_data):
    for data in [sin_cos_data, linear_quadratic_data, inverse_polynomial_data]:
        (x, y1), (x, y2), expected_intersections = data

        # None Excat Tolernace - due to linear interpolation in the function
        # The accuracy depends heavily point concentration of the data as using linear interpolation
        # Need to detemine what is a acceptable pt concentration to get accurate results from numpy implementation
        # or just look at my use case, which is 10 hz minimum
        # it will be bad with non-uniform or non-linear data such as linear_quadratic_data.

        ABSOLUTE_TOLERANCE = 8e-2  # +- 0.08

        # Call the function
        intersections = BaseStandardOperator.find_intersections((x, y1), (x, y2), method="linear_interpolation")
        # This will call on the numpy implementation of the find_intersections function

        # Assert that the number of intersections matches and values are close to expected
        assert len(intersections) == len(expected_intersections)
        for actual, expected in zip(intersections, expected_intersections):
            assert actual[0] == pytest.approx(expected[0], abs=ABSOLUTE_TOLERANCE)
            assert actual[1] == pytest.approx(expected[1], abs=ABSOLUTE_TOLERANCE)


# Test 2: Basic intersection detection with exact method
def test_find_intersections_basic_exact(sin_cos_data, linear_quadratic_data, inverse_polynomial_data):
    for data in [sin_cos_data, linear_quadratic_data, inverse_polynomial_data]:
        (x, y1), (x, y2), expected_intersections = data

        # None Excat Tolernace - due to linear interpolation in the function
        ABSOLUTE_TOLERANCE = 1e-3  # +- 0.001

        # Call the function using the exact method
        intersections = BaseStandardOperator.find_intersections((x, y1), (x, y2), method="exact")
        # This will call on the shaply implementation of the find_intersections function

        # Sort actual intersections by x-coordinate for comparison
        intersections = sorted(intersections, key=lambda pt: pt[0])

        # Print to inspect if needed (uncomment for debugging)
        print(f"Expected Intersections: {expected_intersections}")
        print(f"Obtained Intersections: {intersections}")

        # Assert that the number of intersections matches and values are close to expected
        assert len(intersections) == len(expected_intersections)
        for actual, expected in zip(intersections, expected_intersections):
            assert actual[0] == pytest.approx(expected[0], abs=ABSOLUTE_TOLERANCE)
            assert actual[1] == pytest.approx(expected[1], abs=ABSOLUTE_TOLERANCE)


# Test 3: Return only the first intersection
def test_find_intersections_first_only(sin_cos_data):
    (x, y1), (x, y2), _ = sin_cos_data

    ABSOLUTE_TOLERANCE = 5e-2  # +- 0.05
    # Linear near 0 this tolerance is fine

    # Call the function with first_only=True
    intersections = BaseStandardOperator.find_intersections(
        (x, y1), (x, y2), method="linear_interpolation", first_only=True
    )

    # Only the first intersection should be returned
    assert len(intersections) == 1
    expected_first_intersection = (np.pi / 4, np.sin(np.pi / 4))
    assert intersections[0][0] == pytest.approx(expected_first_intersection[0], abs=ABSOLUTE_TOLERANCE)
    assert intersections[0][1] == pytest.approx(expected_first_intersection[1], abs=ABSOLUTE_TOLERANCE)
