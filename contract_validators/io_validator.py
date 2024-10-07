import warnings
from pathlib import Path
from typing import Any

from .error_generator import ErrorGenerator


class IOValidator:
    """
    IOValidator provides utilities for validating file paths, extensions, and ensuring that files exist.
    It is generalized to work for any path-related validation.
    """

    @staticmethod
    def _validate_is_path(path: Any, arg_name: str, func_name: str, fatal: bool) -> bool:
        """
        Ensure the given value is a Path object.

        Returns True if the path is valid, otherwise raises an error or warning and returns False.
        """
        if not isinstance(path, Path):
            message = f"{func_name}: '{arg_name}' must be a valid Path object. Given: {type(path).__name__}."
            if fatal:
                raise TypeError(message)
            else:
                warnings.warn(message)
            return False
        return True

    @staticmethod
    def validate_path_exists(path: Path, arg_name: str = "path", func_name: str = "", fatal: bool = True) -> None:
        """Ensure the given path exists."""
        if not IOValidator._validate_is_path(path, arg_name, func_name, fatal):
            return

        if not path.exists():
            message = f"{func_name}: '{arg_name}' must point to an existing path. Given: {path}."
            if fatal:
                raise ErrorGenerator.generate_file_not_found_error(path)
            else:
                warnings.warn(message)

    @staticmethod
    def validate_path_extension(
        path: Path, allowed_extensions: list[str], arg_name: str = "path", func_name: str = "", fatal: bool = True
    ) -> None:
        """Ensure the file has one of the allowed extensions."""
        if not IOValidator._validate_is_path(path, arg_name, func_name, fatal):
            return

        # Normalize extensions to ensure they start with a dot
        allowed_extensions = [ext if ext.startswith(".") else f".{ext}" for ext in allowed_extensions]

        if path.suffix not in allowed_extensions:
            allowed_ext_str = ", ".join(allowed_extensions)
            message = f"{func_name}: '{arg_name}' has an invalid extension '{path.suffix}'. Allowed extensions: {allowed_ext_str}."
            if fatal:
                raise ErrorGenerator.generate_value_error("file extension", arg_name, allowed_ext_str)
            else:
                warnings.warn(message)

    @staticmethod
    def validate_directory(path: Path, arg_name: str = "path", func_name: str = "", fatal: bool = True) -> None:
        """Ensure the given path is a directory."""
        if not IOValidator._validate_is_path(path, arg_name, func_name, fatal):
            return

        if not path.is_dir():
            message = f"{func_name}: '{arg_name}' must be a directory. Given: {path}."
            if fatal:
                raise NotADirectoryError(message)
            else:
                warnings.warn(message)
