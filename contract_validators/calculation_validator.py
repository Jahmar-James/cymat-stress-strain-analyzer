import warnings
from typing import Union

import pandas as pd
from uncertainties import UFloat

from .error_generator import ErrorGenerator


class CalculationValidator:
    """
    CalculationValidator provides specific validation functions used in materials property calculations.
    These methods ensure proper inputs for calculations, such as validating numbers, lists of Series, etc.
    """

    @staticmethod
    def validate_positive_number(
        value: Union[float, int, UFloat], var_name: str = "", func_name: str = "", fatal: bool = True
    ) -> None:
        """
        Ensure that a value is a positive number.

        Raises a ValueError if the value is not positive.
        """
        # Check if value is UFloat and validate its nominal value
        if isinstance(value, UFloat) and value.nominal_value <= 0:
            message = f"{func_name}: '{var_name}' must have a positive nominal value. Received: {value}"
            if fatal:
                raise ValueError(message)
            else:
                warnings.warn(message)
        elif isinstance(value, (float, int)) and value <= 0:
            message = f"{func_name}: '{var_name}' must be a positive number. Received: {value}."
            if fatal:
                raise ErrorGenerator.generate_value_error("number", var_name, "positive number", func_name)
            else:
                warnings.warn(message)

    @staticmethod
    def validate_series_list(
        series_list: list[pd.Series], func_name: str = "", check_index=True, fatal: bool = True
    ) -> None:
        """
        Ensure that a list contains pandas Series with consistent indices.

        Assumptions:
         - 'series_list' is already a list at this point (validated externally).
         - The list is non-empty.

        Raises a ValueError if not all elements are pandas Series or if the Series have inconsistent indices.
        """
        # Check if all elements are pandas Series
        if not all(isinstance(s, pd.Series) for s in series_list):
            message = f"{func_name}: All elements in 'series_list' must be pandas Series. Received: {series_list}."
            if fatal:
                raise ErrorGenerator.generate_value_error("list", "series_list", "pandas.Series", func_name)
            else:
                warnings.warn(message)
            return

        # Ensure no Series is empty
        if any(s.empty for s in series_list):
            message = f"{func_name}: All elements in 'series_list' must not be empty. Received: {series_list}."
            if fatal:
                raise ErrorGenerator.generate_value_error("list", "series_list", "non-empty pandas.Series", func_name)
            else:
                warnings.warn(message)
            return

        if check_index:
            # Ensure that all Series in the list have consistent indices
            index = series_list[0].index
            for idx, s in enumerate(series_list):
                if not s.index.equals(index):
                    message = f"{func_name}: Series at index {idx} has a different index than the first Series."
                    if fatal:
                        raise ValueError(message)
                    else:
                        warnings.warn(message)

    @staticmethod
    def validate_dfs_columns_exist(
        dataframes: list[pd.DataFrame], required_columns: list[str], func_name: str = "", fatal: bool = True
    ) -> None:
        """
        Validate that all DataFrames contain the specified required columns.

        Raises a ValueError if any DataFrame is missing required columns.
        """
        missing_info = []
        for i, df in enumerate(dataframes):
            if not isinstance(df, pd.DataFrame):
                message = (
                    f"{func_name}: 'DataFrame at index {i}' must be a pandas DataFrame. Received: {type(df).__name__}."
                )
                if fatal:
                    raise ErrorGenerator.generate_value_error(
                        "DataFrame", f"DataFrame at index {i}", "pandas.DataFrame", func_name
                    )
                else:
                    warnings.warn(message)
                continue

            # Check for missing columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                df_name = df.name if hasattr(df, "name") else f"DataFrame at index {i}"
                missing_info.append(f"{df_name} is missing columns: {', '.join(missing_columns)}")

        # If missing columns were found, raise or warn
        if missing_info:
            error_message = "\n".join(missing_info)
            if fatal:
                raise ValueError(f"{func_name}: The following DataFrames are missing columns:\n{error_message}")
            else:
                warnings.warn(f"{func_name}: The following DataFrames are missing columns:\n{error_message}")
