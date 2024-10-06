from collections import namedtuple
from typing import Optional, Union
from warnings import warn

import numpy as np
import pandas as pd
import scipy as sp
import uncertainties
from scipy.interpolate import CubicSpline, PchipInterpolator, interp1d
from uncertainties import unumpy as unp

# Define a namedtuple for consistent return format
CalculationResult = namedtuple("CalculationResult", ["value", "uncertainty"])
PeakResult = namedtuple("PeakResult", ["indices", "values", "metadata", "warning"])

from .calculation_validation_helper import ValidationHelper


# SamplePropertyCalculator
class BaseStandardOperator:
    """
    A base class for handling generic operations like calculating stress, strain, and energy absorption.
    Uses static methods, fails loudly on contract violations, and provides an optional conversion factor.
    (This class is intended to be inherited by more specialized classes for specific standards.)

    Will provide all the property calculation methods needed by the SampleGeneric class.
    """

    @staticmethod
    def calculate_cross_sectional_area(
        length: float,
        width: float,
        conversion_factor: float = 1.0,
        length_uncertainty: Optional[Union[float, str]] = None,
        width_uncertainty: Optional[Union[float, str]] = None,
    ) -> CalculationResult:
        """
        Calculate the cross-sectional area of a sample given its length and width.

        Preconditions:
        - `length` and `width` must be positive float values.
        - `conversion_factor` is optional, and defaults to 1. It is used to convert the area into desired units.
        - `length_uncertainty` and `width_uncertainty` are optional; if provided, they should be positive floats or
            relative uncertainties in string format (e.g., '5%').

        Postconditions:
        - Returns the cross-sectional area of the sample, adjusted by `conversion_factor`. If uncertainties are provided,
        returns a `ufloat` representing the area with its uncertainty.
        """
        # Validate inputs
        ValidationHelper.validate_positive_number(length, "Length", "calculate_cross_sectional_area")
        ValidationHelper.validate_positive_number(width, "Width", "calculate_cross_sectional_area")
        ValidationHelper.validate_positive_number(
            conversion_factor, "Conversion factor", "calculate_cross_sectional_area"
        )

        # Convert to ufloat if uncertainties are provided
        if length_uncertainty is not None:
            length = BaseStandardOperator._convert_to_uncertain_values(
                length, length_uncertainty, "Length", "calculate_cross_sectional_area"
            )
        if width_uncertainty is not None:
            width = BaseStandardOperator._convert_to_uncertain_values(
                width, width_uncertainty, "Width", "calculate_cross_sectional_area"
            )

        # Calculate the cross-sectional area (A = length * width)
        area = length * width * conversion_factor
        # Check if the result is a ufloat (Variable)
        if isinstance(area, uncertainties.UFloat):
            # Return nominal value and standard deviation as uncertainty
            return CalculationResult(value=area.nominal_value, uncertainty=area.std_dev)

        # Return the result as a float with zero uncertainty if no ufloat was used
        return CalculationResult(value=area, uncertainty=0.0)

    @staticmethod
    def _convert_to_uncertain_values(
        data: Union[float, pd.Series, uncertainties.UFloat, np.ndarray],
        uncertainty: Optional[Union[float, str, pd.Series]] = None,
        var_name: str = "",
        func_name: str = "",
    ) -> Union[uncertainties.UFloat, np.ndarray]:
        """
        Convert a scalar value or pandas Series to a ufloat or array of ufloats with uncertainties.

        :param data: The value or data series to be converted.
        :param uncertainty: The uncertainty for the value/series.
                            Can be absolute (float), relative percentage (str, e.g., '5%'),
                            or a pandas Series with element-wise uncertainties.
        :param var_name: Name of the variable being processed (optional, for error messages).
        :param func_name: Name of the function calling this helper (optional, for error messages).
        :return: A ufloat or numpy ndarray representing the data with uncertainties.
        """
        # when data is a vector (pandas Series)
        if isinstance(data, (pd.Series, np.ndarray)):
            index = None
            if isinstance(data, pd.Series):
                index = data.index
                data = data.values  # Convert to numpy array for easier handling
            
            # Handle Series input
            if uncertainty is None:
                return unp.uarray(data,0)# Return data with zero uncertainty

            elif isinstance(uncertainty, str) and uncertainty.endswith("%"):
                # Relative uncertainty provided as a percentage string (e.g., '5%')
                try:
                    relative_value = float(uncertainty.strip("%")) / 100.0
                    return unp.uarray(data, data * relative_value)
                except ValueError:
                    raise ValueError(
                        "Invalid relative uncertainty provided as a percentage string. Expected format: '5%' Received: '{uncertainty}'."
                    )
            elif isinstance(uncertainty, (float, int)):
                # Absolute uncertainty provided as a float or int
                if uncertainty <= 0:
                    raise ValueError(
                        f"{func_name}: Invalid absolute uncertainty for {var_name}. Must be a positive value. Received: {uncertainty}"
                    )
                return unp.uarray(data, uncertainty)
            elif isinstance(uncertainty, (pd.Series, np.ndarray)):
                # Element-wise uncertainty provided as a Series
                if index is not None:  # Data was a pandas Series
                    if isinstance(uncertainty, pd.Series) and uncertainty.index.equals(index):
                        return unp.uarray(data, uncertainty.values)
                    else:
                        raise ValueError(f"{func_name}: Data series and uncertainty series must have the same index.")
                
                if isinstance(uncertainty, pd.Series):
                    uncertainty = uncertainty.values # Convert to numpy array for easier handling
                    
                if len(data) != len(uncertainty):
                    raise ValueError(
                        f"{func_name}: Data and uncertainty arrays must have the same length. "
                        f"Data length: {len(data)}, Uncertainty length: {len(uncertainty)}")
                
                return unp.uarray(data, uncertainty)

            else:
                raise ValueError(
                    f"{func_name}: Invalid uncertainty type for {var_name}. "
                    f"Must be float, str, or pd.Series. Received: {type(uncertainty)}"
                )

        # when data is a scalar value
        elif isinstance(data, (float, int)):
            # Handle scalar input
            if uncertainty is None:
                return uncertainties.ufloat(data, 0)  # Return ufloat with zero uncertainty

            elif isinstance(uncertainty, str) and uncertainty.endswith("%"):
                # Relative uncertainty provided as a percentage string (e.g., '5%')
                relative_value = float(uncertainty.strip("%")) / 100.0
                return uncertainties.ufloat(data, data * relative_value)

            elif isinstance(uncertainty, (float, int)) and uncertainty > 0:
                # Absolute uncertainty
                return uncertainties.ufloat(data, uncertainty)

            else:
                raise ValueError(
                    f"{func_name}: Invalid uncertainty for {var_name}. "
                    f"Must be a positive float or a percentage string. Received: {uncertainty}"
                )
        elif isinstance(data, uncertainties.UFloat):
            return data
        else:
            raise TypeError(
                f"{func_name}: Invalid type for data. Must be float, int, or pd.Series. Received: {type(data)}"
            )

    @staticmethod
    def calculate_volume(
        area: float,
        thickness: float,
        area_uncertainty: Optional[Union[float, str]] = None,
        thickness_uncertainty: Optional[Union[float, str]] = None,
    ) -> CalculationResult:
        """
        Calculate the volume of a sample given its area and thickness.
        If uncertainties are provided, calculate the propagated uncertainty in the volume.

        Preconditions:
        - `area` and `thickness` must be positive float values.
        - `area_uncertainty` and `thickness_uncertainty` are optional; if provided, they should be positive floats or
        relative uncertainties in string format (e.g., '5%').

        Postconditions:
        - Returns the volume of the sample. If uncertainties are provided, returns a `ufloat` representing the volume
        with its uncertainty.
        """
        # Validate inputs using updated ValidationHelper
        ValidationHelper.validate_positive_number(area, "Area", "calculate_volume")
        ValidationHelper.validate_positive_number(thickness, "Thickness", "calculate_volume")

        # Apply uncertainties if provided
        if area_uncertainty is not None:
            area = BaseStandardOperator._convert_to_uncertain_values(area, area_uncertainty, "Area", "calculate_volume")
        if thickness_uncertainty is not None:
            thickness = BaseStandardOperator._convert_to_uncertain_values(
                thickness, thickness_uncertainty, "Thickness", "calculate_volume"
            )

        # Calculate the volume (V = area * thickness)
        volume = area * thickness

        if isinstance(volume, uncertainties.UFloat):
            return CalculationResult(value=volume.nominal_value, uncertainty=volume.std_dev)
        
        return CalculationResult(value=volume, uncertainty=0.0)


    @staticmethod
    def calculate_volume_direct(
        length: float, 
        width: float, 
        thickness: float, 
        length_uncertainty: Optional[Union[float, str]] = None, 
        width_uncertainty: Optional[Union[float, str]] = None, 
        thickness_uncertainty: Optional[Union[float, str]] = None
    ) -> CalculationResult:
        """
        Calculate the volume of a sample given its length, width, and thickness.
        If uncertainties are provided, calculate the propagated uncertainty in the volume.

        Preconditions:
        - `length`, `width`, and `thickness` must be positive float values.
        - `length_uncertainty`, `width_uncertainty`, and `thickness_uncertainty` are optional; if provided, they should be 
        positive floats or relative uncertainties in string format (e.g., '5%').

        Postconditions:
        - Returns the volume of the sample. If uncertainties are provided, returns a `ufloat` representing the volume
        with its uncertainty.
        """
        # Validate inputs using ValidationHelper
        ValidationHelper.validate_positive_number(length, "Length", "calculate_volume_direct")
        ValidationHelper.validate_positive_number(width, "Width", "calculate_volume_direct")
        ValidationHelper.validate_positive_number(thickness, "Thickness", "calculate_volume_direct")

        # Apply uncertainties if provided
        if length_uncertainty is not None:
            length = BaseStandardOperator._convert_to_uncertain_values(length, length_uncertainty, "Length", "calculate_volume_direct")
        if width_uncertainty is not None:
            width = BaseStandardOperator._convert_to_uncertain_values(width, width_uncertainty, "Width", "calculate_volume_direct")
        if thickness_uncertainty is not None:
            thickness = BaseStandardOperator._convert_to_uncertain_values(thickness, thickness_uncertainty, "Thickness", "calculate_volume_direct")

        # Calculate the volume (V = length * width * thickness)
        volume = length * width * thickness

        if isinstance(volume, uncertainties.UFloat):
            return CalculationResult(value=volume.nominal_value, uncertainty=volume.std_dev)
        
        return CalculationResult(value=volume, uncertainty=0.0)

    @staticmethod
    def calculate_density(
        mass: float, 
        volume: float, 
        conversion_factor: float = 1.0, 
        mass_uncertainty: Optional[Union[float, str]] = None, 
        volume_uncertainty: Optional[Union[float, str]] = None
    ) -> CalculationResult:
        """
        Calculate the density of a sample given its mass and volume.
        If uncertainties are provided, calculate the propagated uncertainty in the density.

        Preconditions:
        - `mass` and `volume` must be positive float values.
        - `conversion_factor` is optional, and defaults to 1. It is used to convert the density into desired units.
        - `mass_uncertainty` and `volume_uncertainty` are optional; if provided, they should be positive floats or 
        relative uncertainties in string format (e.g., '5%').

        Postconditions:
        - Returns the density of the sample, adjusted by `conversion_factor`. If uncertainties are provided, returns a 
        `ufloat` representing the density with its uncertainty.
        """
        # Validate inputs using updated ValidationHelper
        ValidationHelper.validate_positive_number(mass, "Mass", "calculate_density")
        ValidationHelper.validate_positive_number(volume, "Volume", "calculate_density")
        ValidationHelper.validate_positive_number(conversion_factor, "Conversion Factor", "calculate_density")

        # Apply uncertainties if provided
        if mass_uncertainty is not None:
            mass = BaseStandardOperator._convert_to_uncertain_values(mass, mass_uncertainty, "Mass", "calculate_density")
        if volume_uncertainty is not None:
            volume = BaseStandardOperator._convert_to_uncertain_values(volume, volume_uncertainty, "Volume", "calculate_density")

        # Calculate the density (density = mass / volume)
        density = (mass / volume) * conversion_factor

        if isinstance(density, uncertainties.UFloat):
            return CalculationResult(value=density.nominal_value, uncertainty=density.std_dev)
        
        return CalculationResult(value=density, uncertainty=0.0)


    @staticmethod
    def calculate_stress(
        force_series: pd.Series,
        area: float,
        conversion_factor: float = 1.0,
        inversion_check: bool = True,
        force_uncertainty: Optional[Union[float, str, pd.Series]] = None,
        area_uncertainty: Optional[Union[float, str]] = None,
    ) -> CalculationResult:
        """
        Calculate stress from force and cross-sectional area.

        Preconditions:
        - `force_series` must be a pandas Series of floats/ints representing force values.
        - `area` must be a positive float/int representing the cross-sectional area.
        - `conversion_factor` is optional, and defaults to 1. It is used to convert stress into desired units.
        - `inversion_check` controls whether stress inversion should be performed (for tensile/compression differentiation).

        Postconditions:
        - Returns a pandas Series with stress values in the same units as the input, adjusted by `conversion_factor`.
        - Optionally inverts stress values based on the mean to handle tensile vs. compression tests.
        """
        # Preconditions: Validate inputs
        ValidationHelper.validate_type(force_series, pd.Series, "force_series", "calculate_stress")
        if force_series.empty:
            raise ValueError("force_series must not be empty. Force Series must contain at least one force value.")
        ValidationHelper.validate_positive_number(area, "Area", "calculate_stress")
        ValidationHelper.validate_positive_number(conversion_factor, "Conversion Factor", "calculate_stress")
        
        if force_uncertainty is not None:
            force_series = BaseStandardOperator._convert_to_uncertain_values(force_series, force_uncertainty, "Force", "calculate_stress")
        if area_uncertainty is not None:
            area = BaseStandardOperator._convert_to_uncertain_values(area, area_uncertainty, "Area", "calculate_stress")
            
        # Calculate stress (stress = force / area)
        stress_series = (force_series / area) * conversion_factor

        if isinstance(stress_series, np.ndarray) or isinstance(stress_series.iloc[0], uncertainties.UFloat):
            stress_values = pd.Series(unp.nominal_values(stress_series), name="stress")
            stress_uncertainties = pd.Series(unp.std_devs(stress_series), name="stress uncertainty")
        else:
            stress_values = stress_series.rename("stress")
            # Assume zero uncertainty, use int for smaller memory footprint
            stress_uncertainties = pd.Series(0, name="stress uncertainty", dtype=int)

        # Optionally, invert stress values for correct plotting (tensile vs compression)
        if inversion_check and stress_values.mean() < 0:
            # If the mean stress is negative, assume it's a compression test and invert the values
            stress_values *= -1

        return CalculationResult(value=stress_values, uncertainty=stress_uncertainties)

    @staticmethod
    def calculate_strain(
        displacement_series: pd.Series,
        initial_length: float,
        conversion_factor: float = 1.0,
        inversion_check: bool = True,
        displacement_uncertainty: Optional[Union[float, str, pd.Series]] = None,
        length_uncertainty: Optional[Union[float, str]] = None,
    ) -> CalculationResult:
        """
        Calculate strain from displacement and initial length.

        Preconditions:
        - `displacement_series` must be a pandas Series of floats/ints representing displacement values.
        - `initial_length` must be a positive float/int representing the original length of the sample.
        - `conversion_factor` is optional, and defaults to 1. It is used to convert strain into desired units.
        - `inversion_check` controls whether strain inversion should be performed (for tensile/compression differentiation).

        Postconditions:
        - Returns a pandas Series with strain values in the same units as the input, adjusted by `conversion_factor`.
        - Optionally inverts strain values based on the mean to handle tensile vs. compression tests.
        """
        # Preconditions: Validate inputs
        ValidationHelper.validate_type(displacement_series, pd.Series, "displacement_series", "calculate_strain")

        if displacement_series.empty:
            raise ValueError("displacement_series must not be empty.")

        ValidationHelper.validate_positive_number(initial_length, "Initial Length", "calculate_strain")
        ValidationHelper.validate_positive_number(conversion_factor, "Conversion Factor", "calculate_strain")

        if displacement_uncertainty is not None:
            displacement_series = BaseStandardOperator._convert_to_uncertain_values(
                displacement_series, displacement_uncertainty, "Displacement", "calculate_strain"
            )

        if length_uncertainty is not None:
            initial_length = BaseStandardOperator._convert_to_uncertain_values(
                initial_length, length_uncertainty, "Initial Length", "calculate_strain"
            )

        # Calculate strain (strain = displacement / initial length)
        strain_series = (displacement_series / initial_length) * conversion_factor

        if isinstance(strain_series, np.ndarray) or isinstance(strain_series.iloc[0], uncertainties.UFloat):
            strain_values = pd.Series(unp.nominal_values(strain_series), name="strain")
            strain_uncertainties = pd.Series(unp.std_devs(strain_series), name="strain uncertainty")
        else:
            strain_values = strain_series.rename("strain")
            # Assume zero uncertainty, use int for smaller memory footprint
            strain_uncertainties = pd.Series(0, name="strain uncertainty", dtype=int)

        # Optionally, invert strain values for correct plotting (tensile vs compression)
        if inversion_check and strain_values.mean() < 0:
            # If the mean strain is negative, assume it's a compression test and invert the values
            strain_values *= -1

        return CalculationResult(value=strain_values, uncertainty=strain_uncertainties)

    @staticmethod
    def interpolate_dataframes(
        df_list: list[pd.DataFrame],
        interp_column: str,
        common_axis: pd.Series,
        interpolation_method: str = "linear",
        parent_func_name=None,
        set_index: bool = True,
    ) -> list[pd.DataFrame]:
        """
        Interpolate the data in each DataFrame to a common axis based on the interpolation column.

        Preconditions:
        - `df_list` must be a list of pandas DataFrames.
        - Each DataFrame in `df_list` must contain the `interp_column`.
        - The `interp_column` must be in increasing order. If not, it will be sorted.
        - The `common_axis` must be a pandas Series with the desired axis values for interpolation.

        Parameters:
        - `df_list`: List of pandas DataFrames to interpolate.
        - `interp_column`: The column to use for interpolation.
        - `common_axis`: A pandas Series with the common axis values for interpolation.
        - `interpolation_method`: Method to use for interpolation (default is 'linear').
            Supported methods:
            - 'linear': Linear interpolation between points.
            - 'nearest': Use the nearest available value.
            - 'quadratic': Quadratic interpolation.
            - 'cubic': Cubic interpolation.
            - 'polynomial': Polynomial interpolation (requires specifying an order, e.g., 'polynomial', order=2 for quadratic).

        Postconditions:
        - Returns a list of pandas DataFrames with the interpolated values on the common axis.

        """
        interpolated_dfs = []

        for df in df_list:
            df = df.copy()  # Avoid modifying the original DataFrame
            if not df[interp_column].is_monotonic_increasing:
                if parent_func_name:
                    warn(f"Func [{parent_func_name}] | Sorting DataFrame by '{interp_column}' before interpolation.")
                else:
                    warn(f"Sorting DataFrame by '{interp_column}' before interpolation.")
                df = df.sort_values(by=interp_column)

            # Initialize a new DataFrame to store interpolated values
            interpolated_df = pd.DataFrame()

            # Loop over all columns except the interpolation column
            for col in df.columns:
                if col != interp_column:
                    # Define interpolation function using scipy's interp1d for each column
                    interp_func = interp1d(
                        df[interp_column], df[col], kind=interpolation_method, fill_value="extrapolate"
                    )

                    interpolated_df[col] = interp_func(common_axis)

            # Add the common_axis back as the interpolation column (e.g., 'time')
            interpolated_df[interp_column] = common_axis
            interpolated_df.set_index(interp_column, inplace=set_index)

            interpolated_dfs.append(interpolated_df)

        return interpolated_dfs

    @staticmethod
    def _generate_common_axis(
        dataframes: list[pd.DataFrame],
        reference_column: str,
        axis_step: float,
        axis_start: Optional[float] = None,
        axis_end: Optional[float] = None,
    ) -> pd.Series:
        """Generate a common axis based on the reference column."""
        if axis_start is None:
            axis_start = min(df[reference_column].min() for df in dataframes)
        if axis_end is None:
            axis_end = max(df[reference_column].max() for df in dataframes)

        # Adjust axis_start and axis_end to align with the step size
        axis_start = np.floor(axis_start / axis_step) * axis_step
        axis_end = np.ceil(axis_end / axis_step) * axis_step
        common_axis = pd.Series(np.arange(axis_start, axis_end + axis_step, axis_step), name=reference_column)
        return common_axis

    @staticmethod
    def interpolate_to_custom_axis(
        df: pd.DataFrame,
        custom_array: np.ndarray,
        interp_column: str,
        target_columns: list = [],
        interpolation_method: str = "linear",  # Can be "linear", "cubic", or "pchip"
        extrapolate: bool = True,  # Boolean to control whether extrapolation is enabled
    ) -> pd.DataFrame:
        """
        Interpolate (downsample or upsample) the data to fit a custom axis based on specified columns.

        Parameters:
        - `df`: The pandas DataFrame containing the original data.
        - `custom_array`: A numpy array (or list) of custom values to which the data will be interpolated.
        - `interp_column`: The column used for interpolation.
        - `target_columns`: (Optional) List of columns to interpolate. If not provided, all numeric columns except the `interp_column` will be interpolated.
        - `interpolation_method`: Method to use for interpolation. Can be "linear", "cubic", or "pchip".
        - `extrapolate`: (Optional) Boolean flag to control whether extrapolation is applied for values outside the original range.

        Returns:
        - A new DataFrame that is interpolated to the provided custom array.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame.")

        if interp_column not in df.columns:
            raise ValueError(f"The DataFrame must contain the '{interp_column}' column.")

        if not isinstance(custom_array, (np.ndarray, list)):
            raise TypeError("custom_array must be a numpy array or list.")

        if target_columns:
            target_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if interp_column in target_columns:
                target_columns.remove(interp_column)

        missing_columns = [col for col in target_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"The following columns in 'target_columns' are missing from the DataFrame: {missing_columns}"
            )

        df_copy = df.copy()

        if not df_copy[interp_column].is_monotonic_increasing:
            warn(f"The '{interp_column}' column is not sorted. Sorting the data by '{interp_column}'.")
            df_copy = df_copy.sort_values(by=interp_column)

        interpolated_df = pd.DataFrame({interp_column: custom_array})

        for col in target_columns:
            # Select the interpolation function and apply extrapolation if needed
            if interpolation_method == "linear":
                # Use numpy.polyfit for linear interpolation
                coefficients = np.polyfit(df_copy[interp_column], df_copy[col], 1)
                linear_model = np.poly1d(coefficients)
                interpolated_df[col] = linear_model(custom_array)

            elif interpolation_method == "cubic":
                # Use CubicSpline for cubic interpolation
                cubic_spline = CubicSpline(df_copy[interp_column], df_copy[col], extrapolate=extrapolate)
                interpolated_df[col] = cubic_spline(custom_array)

            elif interpolation_method == "pchip":
                # Use PchipInterpolator for PCHIP interpolation
                pchip_interp = PchipInterpolator(df_copy[interp_column], df_copy[col], extrapolate=extrapolate)
                interpolated_df[col] = pchip_interp(custom_array)

            else:
                raise ValueError(f"Unsupported interpolation method: {interpolation_method}")

        return interpolated_df

    @staticmethod
    def average_dataframes(
        df_list: list,
        avg_columns: Union[str, list],
        interp_column: str,
        step_size: float,
        start: Optional[float] = None,
        end: Optional[float] = None,
        interpolation_method: str = "linear",
        force_interpolation: bool = False,
    ) -> pd.DataFrame:
        """
        Average specified columns from a list of pandas DataFrames, interpolating them to a common axis if their lengths differ.

        Preconditions:
        - `df_list` must be a list of pandas DataFrames.
        - Each DataFrame in `df_list` must contain the columns specified in `avg_columns` and `interp_column`.
        - The specified `step_size` must be a positive number.
        - If `start` and `end` are not provided, they will be calculated from the minimum and maximum of the interpolation column across all DataFrames.
        - The `interp_column` must be in increasing order. If not, it will be sorted.
        - If all DataFrames are of the same length and the `interp_column` is the same across DataFrames, interpolation is skipped unless `force_interpolation` is True.

        Parameters:
        - `df_list`: List of pandas DataFrames to average.
        - `avg_columns`: The column name or list of column names to average across the DataFrames.
        - `interp_column`: The column to use for interpolation.
        - `step_size`: The step size for the common axis.
        - `start`: (Optional) The starting point for the common axis. If not provided, it will use the minimum value across all DataFrames.
        - `end`: (Optional) The ending point for the common axis. If not provided, it will use the maximum value across all DataFrames.
        - `interpolation_method`: Method to use for interpolation (default is 'linear').
            Supported methods:
            - 'linear': Linear interpolation between points.
            - 'nearest': Use the nearest available value.
            - 'quadratic': Quadratic interpolation.
            - 'cubic': Cubic interpolation.
            - 'polynomial': Polynomial interpolation (requires specifying an order, e.g., 'polynomial', order=2 for quadratic).
        - `force_interpolation`: (Optional) If True, force interpolation even when DataFrames are of the same length and have identical `interp_column` values.

        Postconditions:
        - Returns a pandas DataFrame with the common axis and the averaged columns specified in `avg_columns`.
        """
        if isinstance(avg_columns, str):
            avg_columns = [avg_columns]  # Convert to list for consistent handling

        # Preconditions: Validate inputs
        ValidationHelper.validate_type(df_list, list, "df_list", "average_dataframes")
        ValidationHelper.validate_types_in_list(df_list, pd.DataFrame, "df_list", "average_dataframes")

        ValidationHelper.validate_type(interp_column, str, "interp_column", "average_dataframes")
        ValidationHelper.validate_type(interpolation_method, str, "interpolation_method", "average_dataframes")
        ValidationHelper.validate_type(force_interpolation, bool, "force_interpolation", "average_dataframes")

        ValidationHelper.validate_type(avg_columns, list, "avg_columns", "average_dataframes")
        ValidationHelper.validate_non_empty_list(avg_columns, "avg_columns", "average_dataframes")
        ValidationHelper.validate_types_in_list(avg_columns, str, "avg_columns", "average_dataframes")

        # Validate step_size
        ValidationHelper.validate_positive_number(step_size, "Step size", "average_dataframes")

        # Check that all DataFrames contain the columns to be averaged
        ValidationHelper.validate_columns_exist(df_list, avg_columns + [interp_column])

        # Check if interpolation is needed
        same_length: bool = all(len(df) == len(df_list[0]) for df in df_list)
        axis_is_common: bool = all(df[interp_column].equals(df_list[0][interp_column]) for df in df_list)
        # Might only need to check is axis is common as that implies same length

        if same_length and axis_is_common and not force_interpolation:
            # If no interpolation is needed, directly average the columns
            return BaseStandardOperator._calculate_column_averages(df_list, avg_columns, interp_column)

        # Create the common axis for interpolation
        common_axis = BaseStandardOperator._generate_common_axis(df_list, interp_column, step_size, start, end)

        # Interpolate the DataFrames to the common axis
        interpolated_dfs = BaseStandardOperator.interpolate_dataframes(
            df_list, interp_column, common_axis, interpolation_method, "average_dataframes", set_index=False
        )
        # Average the specified columns
        result_df = BaseStandardOperator._calculate_column_averages(
            interpolated_dfs, avg_columns, interp_column, "average_dataframes"
        )
        return result_df

    @staticmethod
    def _calculate_column_averages(
        dataframes: list[pd.DataFrame],
        avg_columns: list[str],
        reference_column: str,
        parent_func_name=None,
    ) -> pd.DataFrame:
        """Calculate the averages of specified columns across multiple DataFrames."""
        result_data = {reference_column: dataframes[0][reference_column]}
        for column_name in avg_columns:
            available_dataframes = [df for df in dataframes if column_name in df.columns]
            if available_dataframes:
                avg_series = pd.concat([df[column_name] for df in available_dataframes], axis=1).mean(axis=1)
                result_data[f"avg_{column_name}"] = avg_series
            else:
                if parent_func_name:
                    warn(f"Func [{parent_func_name}] | Column '{column_name}' not found in one or more DataFrames.")
                else:
                    warn(f"Column '{column_name}' not found in one or more DataFrames.")
        return pd.DataFrame(result_data)

    @staticmethod
    def find_intersections(
        series1: Union[pd.Series, tuple[np.ndarray, np.ndarray]],
        series2: Union[pd.Series, tuple[np.ndarray, np.ndarray]],
        method: str = "linear_interpolation",
        tolerance: Optional[float] = None,
        range: Optional[tuple[float, float]] = None,
        finding_func: Optional[callable] = None,
        first_only: bool = False,
    ) -> list:
        """
        Find the intersection points between two series or arrays.

        Preconditions:
        - `series1` and `series2` must be pandas Series or tuples of numpy arrays.
        - If tuples are provided, they must contain two arrays representing x and y values.

        Parameters:
        - `series1`: The first pandas Series or tuple of numpy arrays.
        - `series2`: The second pandas Series or tuple of numpy arrays.
        - `method`: The method used to find the intersection points. Can be "linear_interpolation" or "numpy".
        - `tolerance`: (Optional) The tolerance value for intersection detection.
        - `range`: (Optional) The range of x-values to consider for intersection detection.

        This method provides two options for finding intersections:
        1. 'linear_interpolation' (default): Uses fast approximate intersection detection with numpy.
        2. 'exact': Uses precise geometric intersection detection with the Shapely library.
        3. Custom function: Allows using a custom function for intersection detection.

        Choose the method based on the following criteria:
        - Use 'linear_interpolation' when the two series share the same x-values, and you need fast performance.
          This method finds approximate intersections using linear interpolation, which is sufficient for many practical applications.
        - Use 'exact' when the two series have different x-values or when precise geometric intersections are required.
          This method is slower but provides accurate intersection points using geometric operations.

        Returns:
        - A list of intersection points as tuples (x, y).
        """

        # Validate the input series and convert them to numpy arrays
        ValidationHelper.validate_type(series1, (pd.Series, tuple), "series1", "find_intersections")
        ValidationHelper.validate_type(series2, (pd.Series, tuple), "series2", "find_intersections")

        # Convert series1 and series2 to numpy arrays using the helper function
        x1, y1 = BaseStandardOperator._convert_series_to_arrays(series1)
        x2, y2 = BaseStandardOperator._convert_series_to_arrays(series2)

        # Apply range restrictions using the helper function
        x1, y1 = BaseStandardOperator._apply_range_mask(x1, y1, range)
        x2, y2 = BaseStandardOperator._apply_range_mask(x2, y2, range)

        if finding_func is not None and callable(finding_func):
            try:
                return finding_func(x1, y1, x2, y2)
            except Exception as e:
                raise ValueError(f"Error occurred while using the custom finding function: {e}")

        # Select the appropriate intersection method
        if method == "linear_interpolation":
            return BaseStandardOperator._find_intersections_numpy(x1, y1, x2, y2, tolerance, first_only)
        elif method == "exact":
            return BaseStandardOperator._find_intersections_shapely(x1, y1, x2, y2, first_only)
        else:
            raise ValueError(f"Unknown method: {method}. Supported methods are 'linear_interpolation' and 'exact'.")

    @staticmethod
    def _convert_series_to_arrays(
        series: Union[pd.Series, tuple[np.ndarray, np.ndarray]],
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert a pandas Series or a tuple of (x, y) values into separate x and y numpy arrays.
        """
        if isinstance(series, pd.Series):
            x = series.index.values
            y = series.values
        else:
            x, y = series
        return x, y

    @staticmethod
    def _apply_range_mask(
        x: np.ndarray, y: np.ndarray, range: Optional[tuple[float, float]]
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Apply a range mask to limit the data to a specified range of x values.
        """
        if range is not None:
            start, end = range
            mask = (x >= start) & (x <= end)
            return x[mask], y[mask]
        return x, y

    @staticmethod
    def _find_intersections_numpy(
        x1: np.ndarray,
        y1: np.ndarray,
        x2: np.ndarray,
        y2: np.ndarray,
        tolerance: Optional[float] = 1e-6,
        first_only: bool = False,
    ) -> list:
        """
        Find approximate intersections using numpy for fast performance.

        This method finds intersections by detecting sign changes in the difference between
        the two curves (y1 - y2) over a common set of x-values (x1). It assumes that both
        curves are defined over the same set of x-values.

        - The difference `y_diff = y1 - y2` is calculated at each point on the common x-axis.
        - Sign changes in `y_diff` indicate potential intersections.
        - For each sign change, the x-coordinate of the intersection is calculated using linear interpolation.
        - The y-coordinate is approximated as the midpoint between the two y-values at the intersection.

        **Complexity**:
        - Time: O(n), where n is the number of data points.
        - Space: O(n).

        **Use Case**:
        - Best suited for cases where both series share the same x-values and fast,
          approximate intersection detection is sufficient.

        Returns:
        - A list of approximate intersection points as tuples (x, y).
        """
        y_diff = y1 - y2
        sign_changes = np.where(np.diff(np.sign(y_diff)))[0]
        intersections = []
        for idx in sign_changes:
            x_intersect = (x1[idx] * y_diff[idx + 1] - x1[idx + 1] * y_diff[idx]) / (y_diff[idx + 1] - y_diff[idx])
            y_intersect = (y1[idx] + y1[idx + 1]) / 2

            if tolerance is None or abs(y_diff[idx]) <= tolerance:
                intersections.append((x_intersect, y_intersect))
                if first_only:
                    break  # Return only the first intersection found
        return intersections

    @staticmethod
    def _find_intersections_shapely(
        x1: np.ndarray, y1: np.ndarray, x2: np.ndarray, y2: np.ndarray, first_only: bool = False
    ) -> list:
        """
        Find exact intersections using Shapely for precise geometric operations.

        This method constructs geometric LineString objects from the two curves and uses Shapely's
        intersection functionality to find precise geometric intersection points.

        - LineString objects are created from the (x, y) coordinates of each curve.
        - Shapely's `intersection` method is used to find all intersection points.
        - The method supports single points, multiple points, and collections of geometries.

        **Complexity**:
        - Time: O(n * log(n)), where n is the number of data points (depends on the geometric complexity).
        - Space: O(n).

        **Use Case**:
        - Best suited for cases where the two series have different x-values or when precise
          geometric intersections are required, such as for complex curves or geometries.

         Returns:
            A list of exact intersection points as tuples (x, y).
        """
        from shapely.geometry import GeometryCollection, LineString, MultiLineString, MultiPoint, Point

        line1 = LineString(np.column_stack((x1, y1)))
        line2 = LineString(np.column_stack((x2, y2)))
        intersection = line1.intersection(line2)
        intersections = []

        if isinstance(intersection, Point):
            intersections.append((intersection.x, intersection.y))
        elif isinstance(intersection, MultiPoint):
            for point in intersection.geoms:
                intersections.append((point.x, point.y))
        elif isinstance(intersection, (MultiLineString, GeometryCollection)):
            for geom in intersection.geoms:
                if isinstance(geom, Point):
                    intersections.append((geom.x, geom.y))
                elif isinstance(geom, LineString):
                    intersections.extend([(pt.x, pt.y) for pt in geom.coords])

        return intersections

    @staticmethod
    def calculate_derivative(
        data_series: pd.Series,
        independent_variable: Optional[pd.Series] = None,
        method: Union[str, callable] = "central",
        order: int = 1,
        uncertainty_y: Optional[Union[float, str, pd.Series]] = None,
        uncertainty_x: Optional[Union[float, str, pd.Series]] = None,
        **kwargs,
    ) -> CalculationResult:
        """
        Calculate the first derivative of a data series using finite differences with optional uncertainty handling.

        Preconditions:
        - `data_series` must be a pandas Series of numeric values.
        - `independent_variable` is optional and must be a pandas Series with the independent variable values.
        - `step_size` is optional and can be a float or an array of step sizes.
        - `method` can be a string ('central', 'forward', 'backward') or a callable function.
        - `order` specifies the order of the derivative (1 for first derivative, 2 for second derivative, etc.).
        - `uncertainty` is optional and can be a float, a string (percentage), or a pandas Series with uncertainties.

        Postconditions:
        - Returns a CalculationResult namedtuple with the derivative values and uncertainties (if provided).
        - Drops NaN values and keeps the same index as the input data series.
        """

        # Validate and prepare data and independent series
        ValidationHelper.validate_positive_number(order, "Order", "calculate_derivative")
        ValidationHelper.validate_type(data_series, pd.Series, "data_series", "calculate_derivative")
        data_series = data_series.copy()

        if independent_variable is not None:
            ValidationHelper.validate_type(
                independent_variable, pd.Series, "independent_variable", "calculate_derivative"
            )
            independent_variable = independent_variable.copy()
            if not data_series.index.equals(independent_variable.index):
                raise ValueError("Data series and independent variable must have the same index.")
            independent_values = independent_variable.values
        else:
            independent_values = data_series.index.values

        name = data_series.name if independent_variable is None else f"{data_series.name}-{independent_variable.name}"

        # Convert data_series to numpy array and handle uncertainty conversion if applicable
        data_values :np.ndarray = data_series.values
        
        # Handle uncertainty for data (uncertainty_y)
        if uncertainty_y is not None:
            data_values = BaseStandardOperator._convert_to_uncertain_values(
                data_values, uncertainty_y, data_series.name, "calculate_derivative"
            )

        # Handle uncertainty for independent variable (uncertainty_x)
        if uncertainty_x is not None:
            independent_values = BaseStandardOperator._convert_to_uncertain_values(
                independent_values, uncertainty_x, independent_variable.name, "calculate_derivative"
            )

        # Calculate the derivative of the specified order
        derivative_values = None # Temporary to ensrue var is defined
        for _ in range(order):
            derivative_values = BaseStandardOperator._apply_differentiation_method(
                data_values, independent_values, method, **kwargs
            )
            
        if derivative_values is None:
            raise ValueError(f"Error occurred while calculating the derivative of order {order}.")

        # Handle uncertainty extraction if ufloat objects are present
        if isinstance(derivative_values[0], uncertainties.UFloat):
            nominal_derivative = unp.nominal_values(derivative_values)  # Renamed from `derivative_nominal`
            derivative_uncertainties = unp.std_devs(derivative_values)
        else:
            nominal_derivative = derivative_values
            derivative_uncertainties = np.zeros_like(derivative_values)

        # Create output series with proper index alignment
        derivative_series = pd.Series(nominal_derivative, index=data_series.index, name=f"{name}_derivative")
        derivative_uncertainty_series = pd.Series(
            derivative_uncertainties, index=data_series.index, name=f"{name}_derivative_uncertainty"
        )

        # Drop NaN values while preserving index alignment
        derivative_series = derivative_series.dropna()
        derivative_uncertainty_series = derivative_uncertainty_series.dropna()

        return CalculationResult(derivative_series, derivative_uncertainty_series)

    @staticmethod
    def _apply_differentiation_method(
        y_data: np.ndarray, x_data: np.ndarray, method: Union[str, callable], **kwargs
    ) -> np.ndarray:
        """
        Apply the chosen differentiation method to the y_data array.
        """
        if isinstance(method, str):
            if method == "central":
                # f(x) = (f(x+h) - f(x-h)) / 2h | 1st order Taylor expansion | O(h^2) Error
                if isinstance(x_data[0], uncertainties.UFloat) or isinstance(y_data[0], uncertainties.UFloat):
                    return central_difference_with_uncertainty(y_data, x_data)
                return np.gradient(y_data, x_data, **kwargs)
            
            elif method == "forward":
                # f(x) = (f(x+h) - f(x)) / h | 1st order Taylor expansion | O(h) Error
                derivative_values = np.diff(y_data) / np.diff(x_data)
                derivative_values = np.append(derivative_values, derivative_values[-1])  # Repeat last value for alignment
                return np.array(derivative_values)
            elif method == "backward":
                # f(x) = (f(x) - f(x-h)) / h | 1st order Taylor expansion | O(h) Error
                derivative_values = np.diff(y_data) / np.diff(x_data)
                derivative_values = np.insert(derivative_values, 0, derivative_values[0])  # Repeat first value for alignment
                return np.array(derivative_values)
            else:
                raise ValueError(
                    f"Unknown differentiation method: {method}. Choose 'central', 'forward', or 'backward'."
                )
        elif callable(method):
            try:
                return method(y_data, x_data, **kwargs)
            except Exception as e:
                raise ValueError(f"Error occurred while applying custom differentiation method: {e}")
        else:
            raise ValueError(f"Invalid method type: {type(method)}. Must be a string or callable function.")

    @staticmethod
    def calculate_integral(
        data_series: pd.Series,
        independent_variable: Optional[pd.Series] = None,
        method: Union[str, callable] = "trapezoidal",
        integration_range: Optional[tuple] = None,
        uncertainty_y: Optional[Union[float, str, pd.Series]] = None,
        uncertainty_x: Optional[Union[float, str, pd.Series]] = None,
        **kwargs,
    ) -> CalculationResult:
        """
        Calculate the numerical integral of a data series over a specified range using various integration methods.

        Preconditions:
        - `data_series` must be a pandas Series of numeric values.
        - `independent_variable` is optional and must be a pandas Series with the independent variable values.
        - `method` can be a string ('trapezoidal', 'simpson') or a callable function for custom integration.
        - `integration_range` is optional and defines the range within the independent variable to perform integration.
        - `uncertainty` is optional and can be a float, a string (percentage), or a pandas Series with uncertainties.

        Postconditions:
        - Returns a CalculationResult namedtuple with the integrated value and uncertainties (if provided).
        - If integration_range is provided, integrates only over the specified range.
        """

        # Validate and prepare data and independent series
        ValidationHelper.validate_type(data_series, (pd.Series,np.ndarray), "data_series", "calculate_integral")
        if isinstance(data_series, np.ndarray):
            data_series = pd.Series(data_series, name="y_data")
            
        data_series = data_series.copy()
        if independent_variable is not None:
            ValidationHelper.validate_type( independent_variable,  (pd.Series,np.ndarray), "independent_variable", "calculate_integral")
            if isinstance(independent_variable, np.ndarray):
                independent_variable = pd.Series(independent_variable, name="x_data")
            independent_variable = independent_variable.copy()
            if not data_series.index.equals(independent_variable.index):
                raise ValueError("Data series and independent variable must have the same index.")
            independent_values = independent_variable.values
        else:
            independent_values = data_series.index.values

        # Apply range restrictions using the helper function
        if integration_range is not None:
            independent_values = BaseStandardOperator._apply_range_mask(independent_values, integration_range)

        # Extract data values and handle uncertainty conversion if applicable
        data_values = data_series.values
        if uncertainty_y is not None:
            data_values = BaseStandardOperator._convert_to_uncertain_values(
                data_values, uncertainty_y, data_series.name, "calculate_integral"
            )
        
        if uncertainty_x is not None:
            independent_values = BaseStandardOperator._convert_to_uncertain_values(
                independent_values, uncertainty_x, independent_variable.name, "calculate_integral"
            )

        # Calculate the integral using the specified method
        integral_value = BaseStandardOperator._apply_integration_method(
            data_values, independent_values, method, **kwargs
        )

        # Handle uncertainty extraction if ufloat objects are present
        if isinstance(integral_value, uncertainties.UFloat):
            nominal_integral = integral_value.nominal_value
            integral_uncertainty = integral_value.std_dev
        else:
            nominal_integral = integral_value
            integral_uncertainty = 0.0

        # Return Value should be a scalar, not an array
        return CalculationResult(nominal_integral, integral_uncertainty)

    @staticmethod
    def _apply_integration_method(
        data: np.ndarray, independent_variable: np.ndarray, method: Union[str, callable], **kwargs
    ) -> float:
        """
        Apply the chosen integration method to the data array.
        """
        if isinstance(method, str):
            if method == "trapezoidal":
                return np.trapz(data, independent_variable, **kwargs)
            elif method == "simpson":
                try:
                    return sp.integrate.simps(data, independent_variable, **kwargs)
                except TypeError:
                    print(f"Simpson's Rule does not support uncertainties Natively. Calculating manually.")
                    # Manually calculate uncertainty using simpson_uncertainty function
                    nominal_data = unp.nominal_values(data)
                    nominal_independent = unp.nominal_values(independent_variable)
                    
                    nominal_integral = sp.integrate.simps(nominal_data, nominal_independent, **kwargs)
                    integral_uncertainty = simpson_uncertainty(data, independent_variable)
                    
                    # Return integral with uncertainty
                    return uncertainties.ufloat(nominal_integral, integral_uncertainty)
            else:
                raise ValueError(f"Unknown integration method: {method}. Choose 'trapezoidal' or 'simpson'.")
        elif callable(method):
            try:
                return method(data, independent_variable, **kwargs)
            except Exception as e:
                raise ValueError(f"Error occurred while applying custom integration method: {e}")
        else:
            raise ValueError(f"Invalid method type: {type(method)}. Must be a string or callable function.")
         
    def calculate_cumulative_integral(
        data_series: pd.Series,
        independent_variable: Optional[pd.Series] = None,
        method: Union[str, callable] = "trapezoidal",
        uncertainty_y: Optional[Union[float, str, pd.Series]] = None,
        uncertainty_x: Optional[Union[float, str, pd.Series]] = None,
        initial: Optional[float] = 0,
        dx: float = 1.0,
        **kwargs
        ) -> tuple[pd.Series, Optional[pd.Series]]:
        """
        Calculate the cumulative integral of a data series at each point.

        Parameters:
        - data_series: pd.Series of numeric values representing the y-values to be integrated.
        - independent_variable: Optional pd.Series of the independent variable (x-values).
        - method: Integration method ('trapezoidal', 'simpson', or callable).
        - uncertainty_y: Optional uncertainty in y-values (can be float, str, or pd.Series).
        - uncertainty_x: Optional uncertainty in x-values (can be float, str, or pd.Series).

        Returns:
        - pd.Series: Series representing the cumulative integral at each point.
        """
        
        # Validate and prepare data and independent series
        ValidationHelper.validate_type(data_series, pd.Series, "data_series", "calculate_cumulative_integral")
        ValidationHelper.validate_type(initial, (int, float), "initial", "calculate_cumulative_integral")
        ValidationHelper.validate_positive_number(dx, "dx", "calculate_cumulative_integral")
        
        data_series = data_series.copy()
        
        if independent_variable is None:
            ValidationHelper.validate_type(independent_variable, pd.Series, "independent_variable", "calculate_cumulative_integral")
            independent_variable = independent_variable.copy()
            # Use the index of data_series as independent variable
            independent_variable = data_series.index
        elif len(independent_variable) != len(data_series):
            # Check if independent_variable and data_series have the same length
            raise ValueError("The length of independent_variable must match the length of data_series.")
        
        # Convert independent and dependent variables to numpy arrays
        x_values = independent_variable.values
        y_values = data_series.values
        
        # Convert to uncertainty objects if needed
        if uncertainty_y is not None:
            y_values = BaseStandardOperator._convert_to_uncertain_values(y_values, uncertainty_y, data_series.name, "calculate_cumulative_integral")
        if uncertainty_x is not None:
            x_values = BaseStandardOperator._convert_to_uncertain_values(x_values, uncertainty_x, independent_variable.name, "calculate_cumulative_integral")
        
        # Select and compute cumulative integral based on method
        if method == "trapezoidal":
            cumulative_integral = sp.integrate.cumulative_trapezoid(y_values, x_values, dx=dx, initial=initial)
        elif method == "simpson":
            try:
                cumulative_integral = sp.integrate.cumulative.simps(y_values, x_values, dx=dx, initial=initial)
            except TypeError:
                raise ValueError("Simpson's Rule does not support uncertainties Natively. Calculating manually.| not implemented yet.")
        else:
            raise ValueError(f"Unknown integration method: {method}. Choose 'trapezoidal' or 'simpson'.")
        
        # if uncertainties are present, convert the first element to UFloat with 0 uncertainty
        if uncertainty_x is not None or uncertainty_y is not None:
            cumulative_integral[0] = uncertainties.ufloat(unp.nominal_values(cumulative_integral[0]), 0)
        
        # Extract nominal values and uncertainties if using UFloat
        if isinstance(cumulative_integral[0], uncertainties.UFloat):
            cumulative_integral_nominal = unp.nominal_values(cumulative_integral)
            cumulative_integral_uncertainty = unp.std_devs(cumulative_integral)
            result_series = pd.Series(cumulative_integral_nominal, index=independent_variable, name="Cumulative Integral")
            result_series_uncertainty = pd.Series(cumulative_integral_uncertainty, index=independent_variable, name="Integral Uncertainty")
            return result_series, result_series_uncertainty
        
        # Return result as a pandas series using independent_variable as index
        return pd.Series(cumulative_integral, index=independent_variable, name="Cumulative Integral"), None


    # General Helper Functions

    @staticmethod
    def _get_dataframes_with_required_columns(
        dataframes: list[pd.DataFrame], required_columns: list[str]
    ) -> list[pd.DataFrame]:
        return [df for df in dataframes if all(column_name in df.columns for column_name in required_columns)]

    # TODO: Implement the following methods

    @staticmethod
    def peak_finder(
        data: Union[np.ndarray, pd.Series],
        expected_peaks: Optional[int] = None,
        region: Optional[tuple] = None,
        height: Optional[float] = None,
        # Default values through experimentation wtih data
        distance: Optional[float] = None, # 10
        prominence: Optional[float] = None, # 0.25
    ) -> PeakResult:
        """
        Find peaks in the provided data.
        
        Preconditions:
        - The data must be a numpy array or pandas Series of numeric values.
        - The expected number of peaks must be a positive integer.
        - The region must be a tuple of (start, end) indices.
        - The height, distance, and prominence must be positive float values.
        
        Postconditions:
        - Returns a PeakResult namedtuple with the peak indices and peak values.
        
        Assumptions:
        - The data is assumed to be a 1D array or Series.
        
        Returns:
        - PeakResult: Named tuple containing indices, values, metadata, and any warnings.
        """
        # Validate inputs
        ValidationHelper.validate_type(data, (np.ndarray, pd.Series), "data", "peak_finder")
        if isinstance(data, pd.Series):
            data = data.values
        
        if expected_peaks:
            ValidationHelper.validate_positive_number(expected_peaks, "Expected peaks", "peak_finder")
        if region:
            ValidationHelper.validate_type(region, tuple, "region", "peak_finder")
        if height:
            ValidationHelper.validate_positive_number(height, "Height", "peak_finder")
        if distance:
            ValidationHelper.validate_positive_number(distance, "Distance", "peak_finder")
        if prominence:
            ValidationHelper.validate_positive_number(prominence, "Prominence", "peak_finder")
        
        # Mask the data based on the specified region
        if region:
            start, end = region
            data = data[start:end]
        
        # Detect peaks using scipy's find_peaks
        peaks, properties = sp.signal.find_peaks(data, height=height, distance=distance, prominence=prominence)
        peak_values = data[peaks]
        
        warning_message = None
        if expected_peaks is not None and len(peaks) > expected_peaks:
            warning_message = f"Detected {len(peaks)} peaks, which is more than the expected {expected_peaks}. Consider using a filtering function."
            
        
        metadata = {
            "prominences": properties.get("prominences", []),
            "heights": properties.get("peak_heights", []),
            "widths": properties.get("widths", [])
        }
        
        return PeakResult(indices=peaks, values=peak_values, metadata=metadata, warning=warning_message)
        
        
        

    @staticmethod
    def calculate_slope_in_region() -> float:
        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def _clip_data_to_range():
        # np.clip(a, a_min, a_max, out=None, **kwargs)
        raise NotImplementedError("Method not implemented yet.")

    def _mask_data_by_condition():
        raise NotImplementedError("Method not implemented yet.")


def central_difference_with_uncertainty(y_data, x_data):
    # Extract nominal values and standard deviations from the uncertainties arrays
    y_nominal = unp.nominal_values(y_data)
    x_nominal = unp.nominal_values(x_data)
    y_std = unp.std_devs(y_data)
    x_std = unp.std_devs(x_data)
    # Calculate the nominal derivative using central difference
    dydx_nominal = np.gradient(y_nominal, x_nominal)
    # Calculate the difference between consecutive x points (dx)
    x_diff = np.diff(x_nominal)
    y_diff = np.diff(y_nominal)
    
    # Calculate uncertainty in dy/dx due to uncertainties in y
    # Here, we use np.abs because the term np.diff(y_nominal) can be negative,
    # but the uncertainty we calculate should be based on the absolute magnitude of change.
    # The division by (x_diff**2) accounts for how the changes in x affect the derivative.
    dydx_uncertainty_y  = np.sqrt((y_std[1:] / x_diff)**2 + (y_std[:-1] / x_diff)**2)
    
    # Calculate uncertainty in dy/dx due to uncertainties in x
    dydx_uncertainty_x = np.abs(y_diff / x_diff**2) * np.sqrt(x_std[:-1]**2 + x_std[1:]**2)
    
    dydx_uncertainty = np.sqrt(dydx_uncertainty_y**2 + dydx_uncertainty_x**2)
    
    dydx_uncertainty_full = np.concatenate((dydx_uncertainty, [dydx_uncertainty[-1]]))
    
    dydx = unp.uarray(dydx_nominal, dydx_uncertainty_full)
    return dydx

def simpson_uncertainty(data, x_values):
    """
    Calculate the uncertainty in the integral using Simpson's rule.
    
    Parameters:
    data (array-like): The array of `ufloat` values representing the y-values with uncertainties.
    x_values (array-like): The array of x-values.
    
    Returns:
    float: The uncertainty in the integral.
    """
    # Extract nominal values and uncertainties from y and x arrays
    y_nominal = unp.nominal_values(data)
    y_uncertainty = unp.std_devs(data)
    x_nominal = unp.nominal_values(x_values)
    x_uncertainty = unp.std_devs(x_values)
    
    n = len(y_nominal) - 1
    if n % 2 != 0:
        raise ValueError("Simpson's rule requires an even number of intervals (n must be odd).")
    
    # Step size (nominal)
    delta_x = (x_nominal[-1] - x_nominal[0]) / n

    # Simpson's rule weights
    weights = np.zeros_like(y_nominal)
    weights[0] = 1
    weights[-1] = 1
    weights[1:-1:2] = 4  # Weights for odd indexed elements
    weights[2:-1:2] = 2  # Weights for even indexed elements
    
    # Calculate uncertainty in the integral due to y-values
    integral_uncertainty_y = (delta_x / 3) * np.sqrt(np.sum((weights * y_uncertainty) ** 2))

    # Calculate uncertainty in the integral due to x-values
    if np.any(x_uncertainty > 0):  # Only calculate if there's uncertainty in x
        integral_uncertainty_x = 0
        # Sum up contributions from uncertainties in delta_x for all intervals
        for i in range(n):
            if i == 0 or i == n:  # First and last points
                delta_x_uncertainty = x_uncertainty[i]
            else:  # Internal points, weight based on Simpson's rule
                delta_x_uncertainty = (x_uncertainty[i-1] + x_uncertainty[i]) / 2
            # Accumulate weighted uncertainty
            integral_uncertainty_x += (delta_x_uncertainty * y_nominal[i])**2
        integral_uncertainty_x = (delta_x / 3) * np.sqrt(integral_uncertainty_x)
    else:
        integral_uncertainty_x = 0

    # Combine uncertainties from y and x
    total_integral_uncertainty = np.sqrt(integral_uncertainty_y**2 + integral_uncertainty_x**2)
    
    return total_integral_uncertainty

if __name__ == "__main__":
    pass
