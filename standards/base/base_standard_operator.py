from typing import Union
from warnings import warn

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline, PchipInterpolator, interp1d


class BaseStandardOperator:
    """
    A base class for handling generic operations like calculating stress, strain, and energy absorption.
    Uses static methods, fails loudly on contract violations, and provides an optional conversion factor.
    """

    @staticmethod
    def calculate_stress(
        force_series: pd.Series,
        area: float,
        conversion_factor: float = 1.0,
        inversion_check: bool = True,
    ) -> pd.Series:
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
        if not isinstance(force_series, pd.Series):
            raise TypeError("force_series must be a pandas Series.")

        if not isinstance(area, (float, int)) or area <= 0:
            raise ValueError("Area must be a positive float or int.")

        if not isinstance(conversion_factor, (float, int)) or conversion_factor <= 0:
            raise ValueError("Conversion factor must be a positive float or int.")

        # Calculate stress (stress = force / area)
        stress_series = (force_series / area) * conversion_factor

        # Optionally, invert stress values for correct plotting (tensile vs compression)
        if inversion_check and stress_series.mean() < 0:
            # If the mean stress is negative, assume it's a compression test and invert the values
            stress_series *= -1

        return stress_series

    @staticmethod
    def calculate_strain(
        displacement_series: pd.Series,
        initial_length: float,
        conversion_factor: float = 1.0,
        inversion_check: bool = True,
    ) -> pd.Series:
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
        if not isinstance(displacement_series, pd.Series):
            raise TypeError("displacement_series must be a pandas Series.")

        if not isinstance(initial_length, (float, int)) or initial_length <= 0:
            raise ValueError("Initial length must be a positive float or int.")

        if not isinstance(conversion_factor, (float, int)) or conversion_factor <= 0:
            raise ValueError("Conversion factor must be a positive float or int.")

        # Calculate strain (strain = displacement / initial length)
        strain_series = (displacement_series / initial_length) * conversion_factor

        # Optionally, invert strain values for correct plotting (tensile vs compression)
        if inversion_check and strain_series.mean() < 0:
            # If the mean strain is negative, assume it's a compression test and invert the values
            strain_series *= -1

        return strain_series

    @staticmethod
    def unit_conversion():
        from pint import UnitRegistry

        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def calculate_slope_in_region() -> float:
        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def _clip_data_to_range():
        # np.clip(a, a_min, a_max, out=None, **kwargs)
        raise NotImplementedError("Method not implemented yet.")

    def _mask_data_by_condition():
        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def _validate_positive_number(number: Union[float, int], var_name: str, parent_func_name=None) -> None:
        """Validate if the provided number is a positive float or int."""
        if not isinstance(number, (float, int)) or number <= 0:
            if parent_func_name:
                raise ValueError(f"Func [{parent_func_name}] | {var_name} must be a positive float or int.")
            else:
                raise ValueError(f"{var_name} must be a positive float or int.")

    @staticmethod
    def _validate_columns_exist(dataframes: list[pd.DataFrame], required_columns: list[str]) -> list[int]:
        """
        Validate that all DataFrames contain the specified required columns.

        Returns:
            A list of index numbers of DataFrames that are missing required columns.
            Raises:
            ValueError with detailed information on missing columns if validation fails.
        """
        missing_info = []

        for i, df in enumerate(dataframes):
            missing_columns = [column_name for column_name in required_columns if column_name not in df.columns]
            if missing_columns:
                df_name = df.name if hasattr(df, "name") else f"DataFrame at index {i}"
                missing_info.append((i, df_name, missing_columns))

        if missing_info:
            error_message = "\n".join(
                [
                    f"{df_name} is missing columns: {', '.join(missing_cols)}"
                    for _, df_name, missing_cols in missing_info
                ]
            )
            raise ValueError(f"The following DataFrames are missing columns:\n{error_message}")

        # Return the indices of DataFrames with missing columns
        return [i for i, _, _ in missing_info]

    @staticmethod
    def _generate_common_axis(
        dataframes: list[pd.DataFrame],
        reference_column: str,
        axis_step: float,
        axis_start: float = None,
        axis_end: float = None,
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
    def interpolate_dataframes(
        df_list: list[pd.DataFrame],
        interp_column: str,
        common_axis: pd.Series,
        interpolation_method: str = "linear",
        parent_func_name=None,
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

            interpolated_dfs.append(interpolated_df)

        return interpolated_dfs

    @staticmethod
    def average_dataframes(
        df_list: list,
        avg_columns: Union[str, list],
        interp_column: str,
        step_size: float,
        start: float = None,
        end: float = None,
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

        # Preconditions: Validate inputs
        if not isinstance(df_list, list) or not all(isinstance(df, pd.DataFrame) for df in df_list):
            raise TypeError("df_list must be a list of pandas DataFrames.")

        if isinstance(avg_columns, str):
            avg_columns = [avg_columns]  # Convert to list for consistent handling

        if not isinstance(avg_columns, list) or not all(isinstance(col, str) for col in avg_columns):
            raise TypeError("avg_columns must be a string or a list of strings.")

        # Validate step_size
        BaseStandardOperator._validate_positive_number(step_size, "Step size", "average_dataframes")

        # Check that all DataFrames contain the columns to be averaged
        BaseStandardOperator._validate_columns_exist(df_list, avg_columns + [interp_column])

        # Check if interpolation is needed
        same_length = all(len(df) == len(df_list[0]) for df in df_list)
        same_interp_column = all(df[interp_column].equals(df_list[0][interp_column]) for df in df_list)

        if same_length and same_interp_column and not force_interpolation:
            # If no interpolation is needed, directly average the columns
            return BaseStandardOperator._calculate_column_averages(df_list, avg_columns, interp_column)

        # Create the common axis for interpolation
        common_axis = BaseStandardOperator._generate_common_axis(df_list, interp_column, step_size, start, end)

        # Interpolate the DataFrames to the common axis
        interpolated_dfs = BaseStandardOperator.interpolate_dataframes(
            df_list, interp_column, common_axis, interpolation_method, "average_dataframes"
        )
        # Average the specified columns
        result_df = BaseStandardOperator._calculate_column_averages(
            interpolated_dfs, avg_columns, interp_column, "average_dataframes"
        )
        return result_df

    @staticmethod
    def interpolate_to_custom_axis(
        df: pd.DataFrame,
        custom_array: np.ndarray,
        interp_column: str,
        target_columns: list = None,
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

        if target_columns is None:
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
    def peak_finder():
        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def intersection_finder():
        from shapely.geometry import LineString, MultiPoint, Point

        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def numerical_integration():
        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def calculate_area_in_region(
        stress_series: pd.Series, strain_series: pd.Series, start_strain: float, end_strain: float
    ) -> float:
        """
        Calculate the area under the curve (energy) within a user-specified strain region.
        """
        mask = (strain_series >= start_strain) & (strain_series <= end_strain)
        region_stress = stress_series[mask]
        region_strain = strain_series[mask]

        # Use trapezoidal integration to calculate the area
        area = np.trapz(region_stress, region_strain)
        raise NotImplementedError("Method not implemented yet. Add integration methods.")

    @staticmethod
    def calculate_first_derivative() -> pd.Series:
        raise NotImplementedError("Method not implemented yet.")

    @staticmethod
    def calculate_second_derivative() -> pd.Series:
        raise NotImplementedError("Method not implemented yet.")


if __name__ == "__main__":
    pass
