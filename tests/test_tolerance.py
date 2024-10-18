import numpy as np
import pandas as pd
import pytest

from standard_base.entities.benchmark import Tolerance


def test_initialization_with_true_values_and_tolerance() -> None:
    tol = Tolerance(true_values=10, tolerances=2)
    assert tol.true_values == 10
    assert tol.tolerances == 2
    assert tol.upper_bounds == 12
    assert tol.lower_bounds == 8


def test_initialization_with_bounds() -> None:
    tol = Tolerance(upper_bounds=12, lower_bounds=8)
    assert tol.true_values == 10
    assert tol.tolerances == 2
    assert tol.upper_bounds == 12
    assert tol.lower_bounds == 8


def test_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        Tolerance(upper_bounds=5, lower_bounds=10)


def test_validation_scalar() -> None:
    tol = Tolerance(true_values=10, tolerances=2)
    assert tol.validate(10) is True
    assert tol.validate(12) is True
    assert tol.validate(7) is False


def test_validation_array() -> None:
    tol = Tolerance(true_values=[10, 20], tolerances=[2, 4])
    assert tol.validate([10, 20]) is True
    assert tol.validate([12, 24]) is True
    assert tol.validate([7, 16]) is False


def test_validation_array_with_scalar_tolerance() -> None:
    tol = Tolerance(true_values=10, tolerances=2)
    data = np.array([9, 10, 11])
    expected = True
    assert np.array_equal(tol.validate(data), expected)


def test_initialization_with_lists() -> None:
    tol = Tolerance(true_values=[10, 20], tolerances=[2, 3])
    assert np.array_equal(tol.upper_bounds, np.array([12, 23]))
    assert np.array_equal(tol.lower_bounds, np.array([8, 17]))


def test_false_validation() -> None:
    tol = Tolerance(true_values=[10, 20], tolerances=[2, 3])
    data = [8, 24]  # Outside the lower bound for the first, within bounds for the second
    result = tol.validate(data)
    assert not result  # Returns False because one of the values is out of bounds
