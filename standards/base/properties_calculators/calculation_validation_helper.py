from typing import Union

import pandas as pd

from uncertainties import Variable

# Define the ValidationHelper class as previously described
class ValidationHelper:
    """Helper class for validation functions used throughout the materials property calculators."""
    
    @staticmethod
    def validate_positive_number(value: Union[float, int, Variable], var_name: str = "", func_name: str = "") -> None:
        """Ensure that a value is a positive number."""
         # Check if value is ufloat and validate its nominal value
        if isinstance(value, Variable) and value.nominal_value <= 0:
                context_info = f" in function [{func_name}]" if func_name else ""
                raise ValueError(f"{var_name} must have a positive nominal value{context_info}. Received: {value}")
        if not isinstance(value, (float, int)) or value <= 0:
            context_info = f" in function [{func_name}]" if func_name else ""
            raise ValueError(f"{var_name} must be a positive float or int{context_info}. Received: {value}")

    @staticmethod
    def validate_non_empty_list(values: list, var_name: str = "", func_name: str = "") -> None:
        """Ensure that a list is non-empty."""
        if not isinstance(values, list) or not values:
            context_info = f" in function [{func_name}]" if func_name else ""
            raise ValueError(f"{var_name} must be a non-empty list{context_info}. Received: {values}")
        
    @staticmethod
    def validate_series_list(series_list: list[pd.Series], func_name: str = "") -> None:
        """Ensure that a list contains pandas Series with consistent indices."""
        if not isinstance(series_list, list) or not series_list:
            raise ValueError(f"{func_name}: Expected a non-empty list of pandas Series. Received: {series_list}")
        if not all(isinstance(s, pd.Series) for s in series_list):
            raise TypeError(f"{func_name}: All elements in the list must be pandas Series.")

        index = series_list[0].index
        for idx, s in enumerate(series_list):
            if not s.index.equals(index):
                raise ValueError(f"{func_name}: Series at index {idx} has a different index than the first Series.")

    @staticmethod
    def validate_columns_exist(dataframes: list[pd.DataFrame], required_columns: list[str], func_name: str = "") -> None:
        """Validate that all DataFrames contain the specified required columns."""
        missing_info = []
        for i, df in enumerate(dataframes):
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                df_name = df.name if hasattr(df, "name") else f"DataFrame at index {i}"
                missing_info.append(f"{df_name} is missing columns: {', '.join(missing_columns)}")

        if missing_info:
            error_message = "\n".join(missing_info)
            raise ValueError(f"{func_name}: The following DataFrames are missing columns:\n{error_message}")
        
    @staticmethod
    def validate_type(value: any, expected_types: Union[type, tuple[type, ...]], var_name: str = "", func_name: str = "") -> None:
        """Ensure that a variable is of the specified type(s)."""
        if not isinstance(value, expected_types):
            expected_type_names = (
                [t.__name__ for t in expected_types] 
                if isinstance(expected_types, tuple) 
                else [expected_types.__name__]
            )
            expected_types_str = ", ".join(expected_type_names)
            context_info = f" in function [{func_name}]" if func_name else ""
            raise TypeError(f"{var_name} must be of type(s) {expected_types_str}{context_info}. Received: {type(value).__name__}")
        
        
    @staticmethod
    def validate_types_in_list(value: list, expected_types: Union[type, tuple[type, ...]], var_name: str = "", func_name: str = "") -> None:
        """Ensure that all elements in a list are of the specified type(s)."""
        if not all(isinstance(v, expected_types) for v in value):
            expected_type_names = (
                [t.__name__ for t in expected_types] 
                if isinstance(expected_types, tuple) 
                else [expected_types.__name__]
            )
            expected_types_str = ", ".join(expected_type_names)
            context_info = f" in function [{func_name}]" if func_name else ""
            raise TypeError(f"All elements in {var_name} must be of type(s) {expected_types_str}{context_info}.")
    
