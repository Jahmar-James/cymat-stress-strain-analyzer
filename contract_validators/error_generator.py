from pathlib import Path
from typing import Any, Optional, Union


class ErrorGenerator:
    """
    ErrorGenerator provides a consistent and descriptive way to raise errors for common scenarios,
    such as file system issues or incorrect data types.

    For error I will catch or raise
    """

    # Global setting to control the default behavior for user-friendliness
    # Set to True to make the default user-friendly
    DEFAULT_USER_FRIENDLY = False

    # Common error messages

    @staticmethod
    def generate_value_error(
        received_values: Any,
        attribute_name: str,
        expected_values: str,
        task: str = "",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[ValueError, str]:
        """
        Generates a ValueError with task and context info.

        Developer-friendly message: Invalid Value for '[attribute_name]' during [task] in function [func_name]. Expected values: [expected_values]. Received: [received_values]
        User-friendly message: Could not [task]. Please enter a valid [expected_values] for [attribute_name].
        """
        task = task if task else "perform an action"

        context_info = f" in function [{func_name}]" if func_name else ""
        value_type = type(received_values).__name__

        # Full developer-friendly message
        full_message = (
            f"Invalid Value for '{attribute_name}' during {task}{context_info}."
            f"\nExpected values: {expected_values}. Received: {received_values} (type: {value_type})."
        )

        # User-friendly version
        user_message = f"Could not {task}. Please enter a valid {expected_values} for {attribute_name}."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else ValueError(error_message)

    @staticmethod
    def generate_required_arg_error(
        arg_name: str,
        task: str = "",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[ValueError, str]:
        """
        Generates an error when a required argument is missing (None).

        Developer-friendly message: Missing required argument '[arg_name]', cannot be None. during [task] in function [func_name].
        User-friendly message: Error: Cannot [task]. Missing required argument [arg_name]. Please check the input is filled and try again.
        """

        task = task if task else "perform an action"
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = f"Missing required argument '{arg_name}', cannot be None. during {task}{context_info}."

        # User-friendly version
        user_message = (
            f"Cannot {task}. Missing required argument {arg_name}. Please check the input is filled and try again."
        )

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else ValueError(error_message)

    @staticmethod
    def generate_type_error(
        expected_type: str,
        received_type: str,
        arg_name: str = "",
        task: str = "",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[TypeError, str]:
        """
        Generates a TypeError with task and context info.

        Developer-friendly message: Invalid data type for '[arg_name]' during [task] in function [func_name]. Expected type: [expected_type]. Received type: [received_type]
        User-friendly message: Error: Unable to [task], please provide a valid [expected_type] for [arg_name].
        """
        task = task if task else "perform an action"
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = f"Invalid data type for '{arg_name}' during {task}{context_info}. Expected type: {expected_type}. Received type: {received_type}."

        # User-friendly version
        user_message = f"Unable to {task}, please provide a valid {expected_type} for {arg_name}."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else TypeError(error_message)

    @staticmethod
    def generate_unexpected_error(
        message: str,
        original_exception: Exception,
        task: str = "perform an action",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[Exception, str]:
        """
        Generates an Exception with task and context info.

        Developer-friendly message: Unexpected error during [task] in function [func_name]: [message]. Original exception: [original_exception]
        User-friendly message: Error: An unexpected error occurred while trying to [task]. Please try again or contact support.
        """
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = (
            f"Unexpected error during {task}{context_info}: {message}. Original exception: {original_exception}"
        )

        # User-friendly version
        user_message = f"An unexpected error occurred while trying to {task}. Please try again or contact support."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else Exception(error_message)

    # File system errors

    @staticmethod
    def generate_permission_error(
        task: str = "",
        path: Optional[Path] = None,
        suggestion: str = "Check file permissions.",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[PermissionError, str]:
        """
        Generates a PermissionError with task, path, and context info.

        Developer-friendly message: Permission denied: Unable to [task] at '[path]' in function [func_name]. [suggestion]
        User-friendly message: Error: Unable to [task]. Please check file permissions.
        """
        task = task if task else "perform an action"
        path_info = f" at '{path}'" if path else ""
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = f"Permission denied: Unable to {task}{path_info}{context_info}. {suggestion}"

        # User-friendly version only needs task and suggestion
        user_message = f"Error: Unable to {task}. Please check file permissions."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else PermissionError(error_message)

    @staticmethod
    def generate_os_error(
        task: str = "",
        path: Optional[Path] = None,
        suggestion: str = "Check disk space or path validity.",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[OSError, str]:
        """
        Generates an OSError with task, path, and context info.

        Developer-friendly message: File system error: Could not [task] at '[path]' in function [func_name]. [suggestion]
        User-friendly message: Error: Unable to [task]. Please check the system configuration or file path.
        """
        task = task if task else "perform an action"
        path_info = f" at '{path}'" if path else ""
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = f"File system error: Could not {task}{path_info}{context_info}. {suggestion}"

        # User-friendly version
        user_message = f"Error: Unable to {task}. Please check the system configuration or file path."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else OSError(error_message)

    @staticmethod
    def generate_file_not_found_error(
        task: str = "",
        path: Optional[Path] = None,
        suggestion: str = "Ensure the file or directory exists.",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[FileNotFoundError, str]:
        """
                Generates a FileNotFoundError with task, path, and context info.
        o
                Developer-friendly message: File not found at '[path]' in function [func_name]. [suggestion]
                User-friendly message: Error: Unable to [task]. The required file was not found.
        """
        task = task if task else "perform an action"

        path_info = f" at '{path}'" if path else ""
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = f"File not found{path_info}{context_info}. {suggestion}"

        # User-friendly version
        user_message = f"Error: Unable to {task}. The required file was not found."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else FileNotFoundError(error_message)

    # Custom data validation errors for calculations

    @staticmethod
    def generate_invalid_list_type_error(
        arg_name: str,
        expected_types: str,
        received_values: list,
        task: str = "",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[TypeError, str]:
        """
        Generates an error when a list contains elements that are not of the expected type(s).

        Developer-friendly message: Invalid data type(s) in list '[arg_name]' during [task] in function [func_name].
                                    Received: [received_values]. All elements must be of the type(s) [expected_types].

        User-friendly message: Cannot [task]. One or more elements in [arg_name] are invalid. Please provide valid [expected_types].

        """

        task = task if task else "perform an action"
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = (
            f"Invalid data type(s) in list '{arg_name}' during {task}{context_info}."
            f"\nReceived: {received_values}. All elements must be of the type(s) {expected_types}."
        )

        # User-friendly version
        user_message = (
            f"Cannot {task}.\nOne or more elements in {arg_name} are invalid. Please provide valid {expected_types}."
        )

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else TypeError(error_message)

    @staticmethod
    def generate_empty_list_error(
        arg_name: str,
        task: str = "",
        func_name: str = "",
        user_friendly: Optional[bool] = None,
        return_as_str: bool = False,
    ) -> Union[ValueError, str]:
        """
        Generates an error when a list is empty.

        Developer-friendly message: Empty list '[arg_name]' during [task] in function [func_name].
        User-friendly message: Error: Cannot [task]. [arg_name] is empty. Please provide a non-empty list.
        """

        task = task if task else "perform an action"
        context_info = f" in function [{func_name}]" if func_name else ""

        # Full developer-friendly message
        full_message = f"Empty list '{arg_name}' during {task}{context_info}."

        # User-friendly version
        user_message = f"Cannot {task}. {arg_name} is empty. Please provide a non-empty list."

        user_friendly = user_friendly or ErrorGenerator.DEFAULT_USER_FRIENDLY

        error_message = user_message if user_friendly else full_message

        return error_message if return_as_str else ValueError(error_message)
