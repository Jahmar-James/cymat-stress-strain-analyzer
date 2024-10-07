from pathlib import Path


class ErrorGenerator:
    """
    ErrorGenerator provides a consistent and descriptive way to raise errors for common scenarios,
    such as file system issues or incorrect data types.
    """

    @staticmethod
    def generate_permission_error(
        task: str, path: Path, suggestion: str = "Check file permissions.", func_name: str = ""
    ) -> PermissionError:
        """
        Generates a custom PermissionError with a specific task, path, and optional function context.

        Args:
        - task (str): The action that failed (e.g., "write to the file").
        - path (Path): The file or directory path where the permission error occurred.
        - suggestion (str): A suggestion for resolving the issue.
        - func_name (str, optional): The name of the function where the error occurred (for context).

        Returns:
        - PermissionError with a detailed message.
        """
        context_info = f" in function [{func_name}]" if func_name else ""
        return PermissionError(f"Permission denied: Unable to {task} at '{path}'{context_info}. {suggestion}")

    @staticmethod
    def generate_os_error(
        task: str, path: Path, suggestion: str = "Check disk space or path validity.", func_name: str = ""
    ) -> OSError:
        """
        Generates a custom OSError with a specific task, path, and optional function context.

        Args:
        - task (str): The action that failed (e.g., "export data").
        - path (Path): The file or directory path where the error occurred.
        - suggestion (str): A suggestion for resolving the issue.
        - func_name (str, optional): The name of the function where the error occurred (for context).

        Returns:
        - OSError with a detailed message.
        """
        context_info = f" in function [{func_name}]" if func_name else ""
        return OSError(f"File system error: Could not {task} at '{path}'{context_info}. {suggestion}")

    @staticmethod
    def generate_file_not_found_error(
        path: Path, suggestion: str = "Ensure the file or directory exists.", func_name: str = ""
    ) -> FileNotFoundError:
        """
        Generates a custom FileNotFoundError with an optional function context.

        Args:
        - path (Path): The file or directory path that could not be found.
        - suggestion (str): A suggestion for resolving the issue.
        - func_name (str, optional): The name of the function where the error occurred (for context).

        Returns:
        - FileNotFoundError with a detailed message.
        """
        context_info = f" in function [{func_name}]" if func_name else ""
        return FileNotFoundError(f"File not found at '{path}'{context_info}. {suggestion}")

    @staticmethod
    def generate_value_error(
        value_type: str, attribute_name: str, expected_types: str, func_name: str = ""
    ) -> ValueError:
        """
        Generates a custom ValueError for unsupported data types with an optional function context.

        Args:
        - value_type (str): The actual type of the value.
        - attribute_name (str): The name of the attribute being validated.
        - expected_types (str): The expected types.
        - func_name (str, optional): The name of the function where the error occurred (for context).

        Returns:
        - ValueError with a detailed message.
        """
        context_info = f" in function [{func_name}]" if func_name else ""
        return ValueError(
            f"Invalid data type '{value_type}' for '{attribute_name}'{context_info}. Expected types: {expected_types}."
        )

    @staticmethod
    def generate_unexpected_error(message: str, original_exception: Exception, func_name: str = "") -> Exception:
        """
        Generates a generic error for unexpected exceptions with an optional function context.

        Args:
        - message (str): A custom message describing the issue.
        - original_exception (Exception): The original exception that caused the failure.
        - func_name (str, optional): The name of the function where the error occurred (for context).

        Returns:
        - Exception with a detailed message.
        """
        context_info = f" in function [{func_name}]" if func_name else ""
        return Exception(f"Unexpected error: {message}{context_info}. Original exception: {original_exception}")
