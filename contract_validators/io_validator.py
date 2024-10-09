import warnings
from pathlib import Path
from typing import Any, Optional

from .error_generator import ErrorGenerator


class IOValidator:
    """
    IOValidator provides utilities for validating file paths, extensions, and ensuring that files exist.
    It is generalized to work for any path-related validation.
    """

    @staticmethod
    def _validate_is_path(
        path: Any,
        arg_name: str,
        func_name: str,
        task: str = "",
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
    ) -> bool:
        """
        Ensure the given value is a Path object.

        Returns True if the path is valid, otherwise raises an error or warning and returns False.
        """
        if not isinstance(path, Path):
            error_message = ErrorGenerator.generate_value_error(
                received_value=path,
                attribute_name=arg_name,
                expected_value="Path object",
                action=task,
                function_name=func_name,
                user_friendly=user_friendly,
                return_message_only=True,
            )

            if fatal:
                raise TypeError(error_message)
            else:
                if isinstance(error_message, Exception):
                    raise ValueError("Set user_friendly to True to get the error message")
                warnings.warn(error_message)
            return False
        return True

    @staticmethod
    def validate_path_exists(
        path: Path,
        arg_name: str = "path",
        func_name: str = "",
        task: str = "",
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
    ) -> None:
        """Ensure the given path exists."""
        if not IOValidator._validate_is_path(path, arg_name, func_name, task, fatal, user_friendly):
            return

        if not path.exists():
            error_message = ErrorGenerator.generate_file_not_found_error(
                file_path=path,
                action=task,
                function_name=func_name,
                user_friendly=user_friendly,
                return_message_only=True,
            )

            if fatal:
                raise FileNotFoundError(error_message)
            else:
                if isinstance(error_message, Exception):
                    raise ValueError("Set user_friendly to True to get the error message")
                warnings.warn(error_message)

    @staticmethod
    def validate_path_extension(
        path: Path,
        allowed_extensions: list[str],
        arg_name: str = "path",
        func_name: str = "",
        task: str = "",
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
    ) -> None:
        """Ensure the file has one of the allowed extensions."""
        if not IOValidator._validate_is_path(path, arg_name, func_name, task, fatal, user_friendly):
            return

        # Normalize extensions to ensure they start with a dot
        allowed_extensions = [ext if ext.startswith(".") else f".{ext}" for ext in allowed_extensions]

        if path.suffix not in allowed_extensions:
            allowed_ext_str = ", ".join(allowed_extensions)
            error_message = ErrorGenerator.generate_value_error(
                received_value=path.suffix,
                attribute_name=arg_name,
                expected_value=f"one of the following extensions: {allowed_ext_str}",
                action=task,
                function_name=func_name,
                user_friendly=user_friendly,
                return_message_only=True,
            )

            if fatal:
                raise ValueError(error_message)
            else:
                if isinstance(error_message, Exception):
                    raise ValueError("Set user_friendly to True to get the error message")
                warnings.warn(error_message)

    @staticmethod
    def validate_directory(
        path: Path,
        arg_name: str = "path",
        func_name: str = "",
        task: str = "",
        fatal: bool = True,
        user_friendly: Optional[bool] = None,
    ) -> None:
        """Ensure the given path is a directory."""
        if not IOValidator._validate_is_path(path, arg_name, func_name, task, fatal, user_friendly):
            return

        if not path.is_dir():
            error_message = ErrorGenerator.generate_value_error(
                received_value=path,
                attribute_name=arg_name,
                expected_value="directory",
                action=task,
                function_name=func_name,
                user_friendly=user_friendly,
                return_message_only=True,
            )

            if fatal:
                raise NotADirectoryError(error_message)
            else:
                if isinstance(error_message, Exception):
                    raise ValueError("Set user_friendly to True to get the error message")
                warnings.warn(error_message)
