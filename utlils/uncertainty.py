"""

Calculate Type A Uncertainty - Use the standard deviation of repeated measurements
Estimate Type B Uncertainty - Gather information on instrument resolution, calibration, and environmental factors.
Combine Uncertainties - Combine Type A and Type B uncertainties to estimate the total uncertainty by take the square root of the sum of the squares of the individual uncertainties.



Default Uncertainty Values for a Typical Mechanical Testing Setup

Measurement	            Assumed Uncertainty	        Description
Force	                ±0.5% of measured value	    For load cell uncertainty
Displacement	        ±0.01 mm	                For extensometer or LVDT sensor
Length/Width/Thickness	±0.1 mm	                    For specimen dimensions
Diameter            	±0.05 mm	                For circular cross-sections
Cross-Sectional Area	±0.5% of calculated value	Based on dimensional measurements
Modulus of Elasticity	±1-2% of calculated value	Combined uncertainty from force and strain
Temperature         	±1°C	                    For standard laboratory conditions
Humidity            	±5% RH	                    For standard laboratory conditions


Based on Instrument Resolution, Calibration Uncertainty, Environmental Conditions, Repeatability and Reproducibility:
 assumptions
    - Instrument Resolutin | For load cells, extensometers, and displacement sensors, use the smallest increment the device can measure as the uncertainty.
    - Calibration Uncertainty | Assume a typical calibration uncertainty for well-maintained equipment.
    - Environmental Conditions | Assume standard laboratory conditions unless otherwise specified.
    - Repeatability and Reproducibility | If repeated measurements are not available, assume a reasonable repeatability based on equipment performance.


Propagation of uncertainty
    - partial derivatives of the function with respect to each variable

"""

from uncertainties import ufloat, unumpy

"""
std_dev = np.std(measurements, ddof=1)  # ddof=1 for sample standard deviation

# Step 2: Type B uncertainty components
resolution_uncertainty = 0.5 / np.sqrt(3)  # Instrument resolution
calibration_uncertainty = 1.0 / 2          # Calibration uncertainty

# Step 3: Combined uncertainty
combined_uncertainty = np.sqrt(std_dev**2 + resolution_uncertainty**2 + calibration_uncertainty**2)
"""
from typing import Optional, Union

import numpy as np
import pandas as pd
from uncertainties import ufloat
from uncertainties import unumpy as unp


class BaseStandardOperator:
    @staticmethod
    def _convert_to_uncertain_series(data: pd.Series, uncertainty: Optional[Union[float, str]]) -> pd.Series:
        """
        Convert a pandas Series to a series of ufloat with uncertainties.

        :param data: The data series.
        :param uncertainty: The uncertainty for the series.
                            Can be absolute (float) or relative percentage (str, e.g., '5%').
        :return: A series of ufloats.
        """
        if uncertainty is None:
            return data
        if isinstance(uncertainty, str) and uncertainty.endswith("%"):
            # Relative uncertainty
            relative_value = float(uncertainty.strip("%")) / 100.0
            return unp.uarray(data, data * relative_value)
        else:
            # Absolute uncertainty
            return unp.uarray(data, uncertainty)

    @staticmethod
    def _convert_to_uncertain_scalar(value: float, uncertainty: Optional[Union[float, str]]) -> ufloat:
        """
        Convert a scalar value to a ufloat with uncertainty.

        :param value: The scalar value.
        :param uncertainty: The uncertainty for the value.
                            Can be absolute (float) or relative percentage (str, e.g., '5%').
        :return: A ufloat with the specified uncertainty.
        """
        if uncertainty is None:
            return value
        if isinstance(uncertainty, str) and uncertainty.endswith("%"):
            # Relative uncertainty
            relative_value = float(uncertainty.strip("%")) / 100.0
            return ufloat(value, value * relative_value)
        else:
            # Absolute uncertainty
            return ufloat(value, uncertainty)
