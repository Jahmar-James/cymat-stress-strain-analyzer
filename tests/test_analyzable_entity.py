import pandas as pd
import pint
import pytest

from data_extraction.mechanical_test_data_preprocessor import ureg
from standards.base.analyzable_entity import AnalyzableEntity

# =============================================================================
# Fixtures
# =============================================================================


class TestableAnalyzableEntity(AnalyzableEntity):
    def plot(self) -> None:
        # Provide a simple implementation for testing, if needed, or pass
        pass

@pytest.fixture
def analyzable_entity_with_default_units():
    """
    Fixture to create an AnalyzableEntity instance with force and displacement data in default units.
    Default units:
    - Force: newton (N)
    - Displacement: millimeter (mm)
    """
    return TestableAnalyzableEntity(
        name="Sample 1",
        length=10.0,  # in millimeters
        width=5.0,  # in millimeters
        thickness=2.0,  # in millimeters
        force=pd.Series([100, 200, 300]),  # Force in newton
        displacement=pd.Series([0.1, 0.2, 0.3]),  # Displacement in millimeters
    )


# =============================================================================
# Unit Handling and Conversion Tests
# =============================================================================


@pytest.mark.parametrize(
    "target_unit, expected_force",
    [
        ("newton", [100, 200, 300]),  # No conversion
        ("kilonewton", [0.1, 0.2, 0.3]),  # 1 kN = 1000 N
    ],
)
def test_get_force_conversion(analyzable_entity_with_default_units, target_unit, expected_force):
    """
    Test force conversion to different units using the `get_force` method.
    The core force values should remain in newtons, while the returned values should be in the requested units.

    Args:
        target_unit (str): The unit to which the force should be converted (e.g., 'newton', 'kilonewton').
        expected_force (list): The expected force values in the target unit.
    """
    # Act
    # converted_force = analyzable_entity_with_default_units.get_force(target_unit)
    analyzable_entity_with_default_units.set_target_unit("force", target_unit)
    converted_force = analyzable_entity_with_default_units.force

    # Assert
    # Check that the converted force matches the expected values
    assert converted_force.equals(
        pd.Series(expected_force)
    ), f"Expected force in {target_unit}: {expected_force}, but got: {converted_force.tolist()}"

    # Verify that the internal _force attribute remains unchanged in newtons
    internal_force = analyzable_entity_with_default_units._force
    assert internal_force.equals(
        pd.Series([100, 200, 300])
    ), f"Internal _force should remain unchanged in newtons, but got: {internal_force.tolist()}"


def test_area_calculation_with_unit_conversion():
    """
    Test that the area is calculated correctly when length and width have different units.
    The calculation should convert width to the same unit as length before computing the area.

    Expected Behavior:
    - `length = 10 mm` and `width = 0.5 cm` (converted to `5 mm`)
    - Calculated area = `length * width = 10 mm * 5 mm = 50 mm^2`
    """
    # Arrange
    entity = TestableAnalyzableEntity(
        name="Sample 2",
        length=10.0,  # Length in millimeters
        width=0.5,  # Width in centimeters, but stored in internal_units as mm
        thickness=2.0,  # Thickness in millimeters (not relevant for this test)
    )
    # Volume and area already | I am not how - Maybe because they are @property

    # Width in centimeters, will be converted to millimeters
    entity.internal_units["width"] = ureg.centimeter
    entity.recalculate_properties("area")  # Recalculate area with the new width unit

    # Act
    calculated_area = entity.area  # Should convert and calculate the area in mm^2

    # Assert
    expected_area = 50.0  # Calculated as 10 mm * 5 mm = 50 mm^2
    assert calculated_area == pytest.approx(
        expected_area, rel=1e-3
    ), f"Expected area: {expected_area} mm^2, but got: {calculated_area} mm^2"
    assert (
        str(entity.internal_units["area"]) == "millimeter ** 2"
    ), f"Expected area units: 'millimeter ** 2', but got: {entity.internal_units['area']}"


def test_reset_target_unit(analyzable_entity_with_default_units):
    """
    Test that resetting the target unit for a property reverts to the internal unit.

    - Set a target unit for force (e.g., kN).
    - Reset the target unit and verify the force is returned in its internal unit (N).
    """
    # Act
    analyzable_entity_with_default_units.set_target_unit("force", "kilonewton")

    # Verify that force is now in kilonewtons
    force_in_kilonewtons = analyzable_entity_with_default_units.force
    assert force_in_kilonewtons.equals(
        pd.Series([0.1, 0.2, 0.3])
    ), f"Force should be in kilonewtons: [0.1, 0.2, 0.3], but got: {force_in_kilonewtons.tolist()}"

    analyzable_entity_with_default_units.reset_target_unit("force")

    # Verify that force is now back to its default unit (newton)
    assert (
        "force" not in analyzable_entity_with_default_units.target_units
    ), "Expected 'force' to have been reset to its internal unit."

    # Check that accessing force now returns in newtons
    force_in_newtons = analyzable_entity_with_default_units._convert_units(
        analyzable_entity_with_default_units._force, "force"
    )
    assert force_in_newtons.equals(
        pd.Series([100, 200, 300])
    ), f"Force should be back in newtons: [100, 200, 300], but got: {force_in_newtons.tolist()}"


# =============================================================================
# Property Calculations Tests
# =============================================================================


def test_stress_calculation_with_real_helpers(analyzable_entity_with_default_units):
    """
    Test that the stress is calculated correctly using the given force and area.
    Expected stress is calculated as: stress = force / area.
    In this test case:
    - force = [100, 200, 300] N
    - area = 10 mm * 5 mm = 50 mm^2
    - Expected stress = [2, 4, 6] N/mm^2 (or MPa)
    """
    # Act
    stress = analyzable_entity_with_default_units.stress

    # Assert
    expected_stress = pd.Series([2, 4, 6], dtype=float)  # Expected stress values in MPa (N/mm^2) - Must be float
    assert stress.equals(expected_stress), f"Expected stress: {expected_stress.tolist()}, but got: {stress.tolist()}"


def test_strain_calculation(analyzable_entity_with_default_units):
    """
    Test that the strain is calculated correctly using displacement and length.
    Expected strain is calculated as: strain = displacement / length.
    In this test case:
    - displacement = [0.1, 0.2, 0.3] mm
    - length = 10.0 mm
    - Expected strain = [0.01, 0.02, 0.03] (dimensionless)
    """
    # Act
    strain = analyzable_entity_with_default_units.strain

    # Assert
    expected_strain = pd.Series([0.01, 0.02, 0.03])  # Expected dimensionless strain values
    assert strain.equals(expected_strain), f"Expected strain: {expected_strain.tolist()}, but got: {strain.tolist()}"


# =============================================================================
# Data Validation and Error Handling Tests
# =============================================================================


def test_missing_length_for_area(analyzable_entity_with_default_units):
    """
    Test that accessing the `area` property raises an error when `length` is not set.
    """
    # Arrange
    analyzable_entity_with_default_units.length = None  # Remove the length attribute
    analyzable_entity_with_default_units._area = None  # Reset the cached area value

    # Expected error: Cannot calculate area for entity 'Sample 1': Length must be a positive float or int.

    # Act & Assert
    with pytest.raises(ValueError, match=r".*Length must be a positive float or int.*"):
        _ = analyzable_entity_with_default_units.area  # Should raise ValueError

    with pytest.raises(ValueError, match=r".*Cannnot calculate area for entity.*"):
        _ = analyzable_entity_with_default_units.area  # Should raise ValueError


def test_zero_width_for_area(analyzable_entity_with_default_units):
    """
    Test that area calculation returns 0 when the width is zero.
    """
    # Arrange
    analyzable_entity_with_default_units.width = 0.0  # Set width to zero

    # Cannnot calculate area for entity 'Sample 1': Func [calculate_cross_sectional_area] | Width must be a positive float or int.
    with pytest.raises(ValueError, match=r".*Width must be a positive float or int.*"):
        _ = analyzable_entity_with_default_units.area

    with pytest.raises(ValueError, match=r".*Cannnot calculate area for entity.*"):
        _ = analyzable_entity_with_default_units.area


def test_accessing_stress_before_area(analyzable_entity_with_default_units):
    """
    Test that accessing `stress` raises an error if `area` cannot be calculated due to missing attributes.

    Reasoning:
    - `stress` calculation depends on `area`, which requires `width` and `length` to be set.
    - If `width` or `length` is missing, `area` cannot be calculated, and attempting to access `stress` should raise an error.

    Expected Behavior:
    - With `width = None`, accessing `stress` should raise a `ValueError` indicating that `area` is required.
    """
    # Remove width, set _area to None to ensure that cached value is not used
    analyzable_entity_with_default_units.width = None
    analyzable_entity_with_default_units._area = None

    # Expected error: Cannot calculate stress for entity 'Sample 1': Cannnot calculate area for entity 'Sample 1': Func [calculate_cross_sectional_area] | Width must be a positive float or int
    with pytest.raises(ValueError, match=r".*Width must be a positive float or int.*"):
        _ = analyzable_entity_with_default_units.stress


def test_accessing_strain_without_length(analyzable_entity_with_default_units):
    """
    Test that accessing `strain` raises an error if `length` is not set.

    Reasoning:
    - `strain` calculation depends on both `displacement` and `length`.
    - If `length` is not set, the method cannot compute `strain`, and accessing it should raise an error.

    Expected Behavior:
    - With `length = None`, accessing `strain` should raise a `ValueError` indicating that `length` is required.
    """
    # Remove length
    analyzable_entity_with_default_units.length = None

    # Expected error: Cannot calculate strain for entity 'Sample 1': Initial Length must be a positive float or int in function [calculate_strain]. Received: None
    with pytest.raises(ValueError, match=r".*Initial Length must be a positive float or int.*"):
        _ = analyzable_entity_with_default_units.strain
