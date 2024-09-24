from typing import Union

import pandas as pd


# Define the ValidationHelper class as previously described
class ValidationHelper:
    """Helper class for validation functions used throughout the GroupAggregationOperator."""

    @staticmethod
    def validate_non_empty_list(values: list, context: str = "") -> None:
        """Ensure that a list is non-empty."""
        if not isinstance(values, list) or not values:
            raise ValueError(f"{context}: Expected a non-empty list.")

    @staticmethod
    def validate_positive_number(value: float, context: str = "") -> None:
        """Ensure that a value is a positive number."""
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError(f"{context}: Expected a positive number.")

    @staticmethod
    def validate_series_list(series_list: list[pd.Series], context: str = "") -> None:
        """Ensure that a list contains pandas Series with consistent indices."""
        if not isinstance(series_list, list) or not series_list:
            raise ValueError(f"{context}: Expected a non-empty list of pandas Series.")
        if not all(isinstance(s, pd.Series) for s in series_list):
            raise TypeError(f"{context}: All elements in `series_list` must be pandas Series.")

        index = series_list[0].index
        if not all(s.index.equals(index) for s in series_list):
            raise ValueError(f"{context}: All Series in `series_list` must have the same index.")

    @staticmethod
    def _validate_positive_number(number: Union[float, int], var_name: str, parent_func_name=None) -> None:
        """Validate if the provided number is a positive float or int."""
        if not isinstance(number, (float, int)) or number <= 0:
            if parent_func_name:
                raise ValueError(f"Func [{parent_func_name}] | {var_name} must be a positive float or int.")
            else:
                raise ValueError(f"{var_name} must be a positive float or int. But got {number}.")

    @staticmethod
    def _validate_columns_exist(dataframes: list[pd.DataFrame], required_columns: list[str]) -> list[int]:
        """
        Validate that all DataFrames contain the specified required columns.

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
