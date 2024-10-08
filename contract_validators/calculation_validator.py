import warnings
from typing import Optional, Union

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
        value: Union[float, int, UFloat],
        var_name: str = "",
        func_name: str = "",
        task: str = "",
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
    ) -> None:
        """
        Ensure that a value is a positive number.

        Raises a ValueError if the value is not positive.
        """
        # Check if value is UFloat and validate its nominal value
        if isinstance(value, UFloat) and value.nominal_value <= 0:
            error_message = ErrorGenerator.generate_value_error(
                value_type="UFloat nominal value",
                attribute_name=var_name,
                expected_types="positive number",
                task=task,
                func_name=func_name,
                user_friendly=user_friendly,
                return_as_str=True,
            )
            if fatal:
                raise ValueError(error_message)
            else:
                warnings.warn(error_message)
        elif isinstance(value, (float, int)) and value <= 0:
            error_message = ErrorGenerator.generate_value_error(
                value_type="number",
                attribute_name=var_name,
                expected_types="positive number",
                task=task,
                func_name=func_name,
                user_friendly=user_friendly,
                return_as_str=True,
            )
            if fatal:
                raise ValueError(error_message)
            else:
                warnings.warn(error_message)

    @staticmethod
    def validate_series_list(
        series_list: list[pd.Series],
        func_name: str = "",
        task: str = "",
        check_index: bool = True,
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
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
            error_message = ErrorGenerator.generate_value_error(
                value_type="list",
                attribute_name="series_list",
                expected_types="pandas.Series",
                task=task,
                func_name=func_name,
                user_friendly=user_friendly,
                return_as_str=True,
            )
            if fatal:
                raise ValueError(error_message)
            else:
                warnings.warn(error_message)
            return

        # Ensure no Series is empty
        if any(s.empty for s in series_list):
            error_message = ErrorGenerator.generate_value_error(
                value_type="list",
                attribute_name="series_list",
                expected_types="non-empty pandas.Series",
                task=task,
                func_name=func_name,
                user_friendly=user_friendly,
                return_as_str=True,
            )
            if fatal:
                raise ValueError(error_message)
            else:
                warnings.warn(error_message)
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
        dataframes: list[pd.DataFrame],
        required_columns: list[str],
        func_name: str = "",
        task: str = "",
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
    ) -> None:
        """
        Validate that all DataFrames contain the specified required columns.

        By defualt 'fatal' is True, raises a ValueError if any DataFrame is missing columns.
        """
        missing_info = []
        for i, df in enumerate(dataframes):
            if not isinstance(df, pd.DataFrame):
                error_message = ErrorGenerator.generate_value_error(
                    value_type=f"DataFrame at index {i}",
                    attribute_name=f"DataFrame at index {i}",
                    expected_types="pandas.DataFrame",
                    task=task,
                    func_name=func_name,
                    user_friendly=user_friendly,
                    return_as_str=True,
                )
                if fatal:
                    raise ValueError(error_message)
                else:
                    warnings.warn(error_message)
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
