import warnings
from typing import Any, Union

import pandas as pd
import uncertainties

from .calculation_validator import CalculationValidator
from .error_generator import ErrorGenerator
from .io_validator import IOValidator


class ContractValidators:
    """
    ContractValidators is responsible for ensuring that input data and application state adhere to expected
    preconditions (before an operation) and postconditions (after an operation), supporting a "design by contract" approach.

    The primary goal of ContractValidators is to catch and report invalid states early, ensuring that inputs and
    outputs meet their contractual obligations. This class provides centralized validation for common tasks such as
    type checking, required argument verification, and list validations, while delegating specialized checks (such as
    file system paths or complex calculation-related validations) to IOValidator and CalculationValidator, respectively.

    Responsibilities:
    -----------------
    - Centralized Validation: Provides a top-level mechanism to validate preconditions and postconditions across
      the application, ensuring consistency in validation logic and error handling.

    - Design by Contract: Follows the "design by contract" methodology, enforcing explicit guarantees on the state
      and type of input data, ensuring that functions receive and return values according to their documented
      requirements.

    - Useful Error Messaging: Generates clear, consistent, and informative error messages to help developers
      identify the exact source of validation failures, allowing for fast debugging and correction.

    - Delegation to Specialized Validators:
        - IOValidator: Delegates validations related to file system paths, file existence, extensions, and directories.
        - CalculationValidator: Delegates validations specific to data structures and calculations, such as checking
          pandas Series indices or DataFrame column existence.

    Features:
    ---------
    - Type Validation: Ensures that variables are of expected types, raising errors if the types do not match.
    - List Validation: Ensures that lists are not empty and that their elements conform to expected types.
    - Required Argument Check: Ensures that required arguments (non-None) are provided to functions.
    - Delegation: Delegates specialized validations to other validators (IOValidator for file paths,
      CalculationValidator for domain-specific calculations).

    Pre-Conditions:
    ---------------
    - Input arguments must meet expected type, structure, and value constraints.
    - Lists must be non-empty where applicable, and file paths must exist when required.

    Post-Conditions:
    ----------------
    - Ensures data integrity after operations, checking that necessary conditions are met before and after function
      execution.
    """

    @staticmethod
    def validate_type(
        value: Any,
        expected_types: Union[type, tuple[type, ...]],
        arg_name: str = "",
        func_name: str = "",
        fatal: bool = True,
    ) -> None:
        """
        Ensure that a variable is of the specified type(s).

        Args:
        - value: The value to check.
        - expected_types: The type(s) that the value is expected to be.
        - arg_name: Name of the argument being validated (to improve error messages).
        - func_name: Name of the function where this validation is being applied (for context).
        - fatal: Whether this error should be fatal (True) or raise a warning (False).

        Raises:
        - TypeError if fatal is True, otherwise raises a warning.
        """
        if not isinstance(value, expected_types):
            expected_type_names = (
                [t.__name__ for t in expected_types] if isinstance(expected_types, tuple) else [expected_types.__name__]
            )
            expected_types_str = ", ".join(expected_type_names)
            message = (
                f"{func_name}: '{arg_name}' must be of type(s) {expected_types_str}. Received: {type(value).__name__}."
            )

            if fatal:
                raise ErrorGenerator.generate_value_error(type(value).__name__, arg_name, expected_types_str, func_name)
            else:
                warnings.warn(message)

    @staticmethod
    def validate_types_in_list(
        values: list,
        expected_types: Union[type, tuple[type, ...]],
        arg_name: str = "",
        func_name: str = "",
        fatal: bool = True,
    ) -> None:
        """
        Ensure that all elements in a list are of the specified type(s).

        Raises a TypeError (or a warning) if any element is not of the expected type(s).
        """
        # Validate if 'values' is a list
        ContractValidators.validate_type(values, list, arg_name, func_name, fatal=fatal)

        # Check if all elements in the list are of the expected types
        if not all(isinstance(v, expected_types) for v in values):
            expected_type_names = (
                [t.__name__ for t in expected_types] if isinstance(expected_types, tuple) else [expected_types.__name__]
            )
            expected_types_str = ", ".join(expected_type_names)
            message = f"{func_name}: All elements in '{arg_name}' must be of type(s) {expected_types_str}. Received: {values}."
            if fatal:
                raise ErrorGenerator.generate_value_error("list", arg_name, expected_types_str, func_name)
            else:
                warnings.warn(message)

    @staticmethod
    def validate_non_empty_list(values: list, arg_name: str = "", func_name: str = "", fatal: bool = True) -> None:
        """
        Ensure that a list is non-empty.

        Raises a ValueError (or a warning) if the list is empty.
        """
        ContractValidators.validate_type(values, list, arg_name, func_name, fatal=fatal)

        if len(values) == 0:
            message = f"{func_name}: '{arg_name}' must be a non-empty list. Received: {values}."
            if fatal:
                raise ErrorGenerator.generate_value_error("list", arg_name, "non-empty list", func_name)
            else:
                warnings.warn(message)

    @staticmethod
    def validate_required_arg(value: Any, arg_name: str = "", func_name: str = "", fatal: bool = True) -> None:
        """
        Ensure that a required argument is not None.

        Args:
        - value: The argument to check.
        - arg_name: Name of the argument being validated (to improve error messages).
        - func_name: Name of the function where this validation is being applied (for context).
        - fatal: Whether this error should be fatal (True) or raise a warning (False).

        Raises:
        - ValueError if fatal is True, otherwise raises a warning.
        """
        if value is None:
            message = f"{func_name}: '{arg_name}' is required and cannot be None."
            if fatal:
                raise ErrorGenerator.generate_value_error("None", arg_name, "non-None value", func_name)
            else:
                warnings.warn(message)

    # IO Validation (delegates to IOValidator)
    @staticmethod
    def validate_path_exists(path: Any, arg_name="path", func_name="", fatal=True):
        """Ensure the given path exists"""
        IOValidator.validate_path_exists(path, arg_name, func_name, fatal)

    @staticmethod
    def validate_path_extension(path: Any, allowed_extensions: list[str], arg_name="path", func_name="", fatal=True):
        """Ensure the file has one of the allowed extensions."""
        IOValidator.validate_path_extension(path, allowed_extensions, arg_name, func_name, fatal)

    @staticmethod
    def validate_directory(path: Any, arg_name="path", func_name="", fatal=True):
        """Ensure the given path is a directory."""
        IOValidator.validate_directory(path, arg_name, func_name, fatal)

    # Calculation Validation (delegates to CalculationValidator)
    @staticmethod
    def validate_positive_number(
        value: Union[float, int, uncertainties.UFloat], var_name: str = "", func_name: str = "", fatal: bool = True
    ) -> None:
        """
        Ensure that a value is a positive number.

        Raises a ValueError if the value is not positive.
        """
        CalculationValidator.validate_positive_number(value, var_name, func_name, fatal)

    @staticmethod
    def validate_series_list(
        series_list: list[pd.Series], func_name: str = "", fatal: bool = True, check_index=True
    ) -> None:
        """
        Ensure that a list contains pandas Series with consistent indices.

        Delegates to CalculationValidator to check index consistency and Series validity.
        """
        ContractValidators.validate_non_empty_list(series_list, "series_list", func_name, fatal)
        CalculationValidator.validate_series_list(series_list, func_name, check_index, fatal)

    @staticmethod
    def validate_dfs_columns_exist(
        dataframes: list[pd.DataFrame], required_columns: list[str], func_name: str = "", fatal: bool = True
    ) -> None:
        """
        Validate that all DataFrames contain the specified required columns.

        Delegates to CalculationValidator to check column existence.
        """
        ContractValidators.validate_non_empty_list(dataframes, "dataframes", func_name, fatal=fatal)
        CalculationValidator.validate_dfs_columns_exist(dataframes, required_columns, func_name, fatal)
