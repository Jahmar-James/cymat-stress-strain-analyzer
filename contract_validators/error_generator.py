from typing import Optional, Union, Any
from pathlib import Path

class ErrorGenerator:
    """
    ErrorGenerator provides a consistent and descriptive way to raise errors for common scenarios,
    such as invalid data types or file system issues. The error messages generated can be either 
    user-friendly or developer-focused, depending on the `user_friendly` flag.
    
    The error messages follow different templates for users and developers:
    
    - **User-Focused Messages**:
        These messages are concise and provide the user with clear instructions on how to fix the problem, 
        without including unnecessary technical details.

    - **Developer-Focused Messages**:
        These messages include detailed information such as the function name, expected and received values, 
        and the type of the received value. This helps developers debug issues effectively.
    """
    # Global setting to control the default behavior for user-friendliness
    DEFAULT_USER_FRIENDLY = False
    
     # Error types and their templates
    USER_TEMPLATE = "{description}\n{next_step}"
    DEV_TEMPLATE = "{context_info}\n{description}\n{debug_info}\n{next_step}"

    @staticmethod
    def _generate_error_message(template_args: dict, user_friendly: bool) -> str:
        """
        Generates an error message based on the template arguments provided.
        
        Args:
        - template_args (dict): Contains the components needed to format the error message:
            - description (dict[str, str]): A dictionary with 'all', 'user', and/or 'dev' keys.
            - next_step (dict[str, str]): A dictionary containing next steps for user and developer.
            - context_info (str): Pre-generated context information.
            - debug_info (str): Debug information (used only for developer messages).
        - user_friendly (bool): If True, generates a user-friendly error message. If False, generates a developer-focused message.
        
        Returns:
        - str: The fully formatted error message.
        """
        if user_friendly:
            # Use 'user' key if it exists, otherwise fallback to 'all'
            description = template_args['description'].get('user', template_args['description']['all'])
            return ErrorGenerator.USER_TEMPLATE.format(
                description=description,
                next_step=template_args['next_step']['user']
            )
        else:
            # Use 'dev' key if it exists, otherwise fallback to 'all'
            description = template_args['description'].get('dev', template_args['description']['all'])
            return ErrorGenerator.DEV_TEMPLATE.format(
                context_info=template_args['context_info'],
                description=description,
                debug_info=template_args.get('debug_info', ""),
                next_step=template_args['next_step']['dev']
            )
    
    @staticmethod
    def _generate_context(context_stmt: dict[str, str], function_name: str, user_friendly ) -> str:
        """
        Generate the context statement for the error message.
        
            Message Format:
            - Developer-Focused: [YYYY-MMM-DD] [context_stmt] in '[function_name]'
            - User-Focused: [context_stmt]    
        """
        key = "user" if user_friendly else "dev"
        context = context_stmt[key]
        
        if key == "dev":
            from datetime import datetime
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            context = f"{timestamp} {context_stmt[key]} in '{function_name}'"
        
        return context if function_name else f"{timestamp} {context_stmt[key]}"
    
    @staticmethod
    def generate_value_error(
        received_value: Any,
        attribute_name: str,
        expected_value: str,
        action: str = "",
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = None
    ) -> Union[ValueError, str]:
        """
        Generate or return a ValueError message for an invalid value.
        
        Developer-Focused Message:
            Conetext: [YYYY-MMM-DD] [Value Error:] in '[function_name]' 
            Description: Unable to complete the [action]. Invalid value '[received_value]' for '[attribute_name]' (expected positive integers, got str). | Description
            Debug Info: Expected: '[expected_value],' Received: '[received_value]'. 
            Next Steps: Fix the input or handle the invalid value. 
            
        User-Focused Message:
            Unable to complete the [action]. Invalid value '[received_value]' for '[attribute_name]' (expected positive integers, got str). | Description
            Enter a valid number. *Optional: [suggestion] 
        """
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly

        # Context information
        context_stmt = {
            "user": "Invalid input.",
            "dev": "ValueError"
        }
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description 
        received_type = type(received_value).__name__  
        description = {
            'all': f"Unable to {action or 'complete the action'}. Invalid value '{received_value}' for '{attribute_name}' (expected {expected_value}, got {received_type}).",
        }
        
        # Debugging information
        if not user_friendly:
            debug_info = f"Expected: '{expected_value}', Received: '{received_value}' (type: {received_type})"
        
        # Next steps
        next_step = {
            "user": "Please provide a valid value." if suggestion is None else f"Please provide a valid value.\nSuggestion: {suggestion}",
            "dev": "Fix the input or handle the invalid value."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
            "debug_info": debug_info if not user_friendly else "",
        }
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else ValueError(message)

    @staticmethod
    def generate_type_error(
        received_value: Any,                    
        expected_type: str,                 
        attribute_name: str,                    
        action: str = "",               
        function_name: str = "",            
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,   
        suggestion: Optional[str] = None     
    ) -> Union[TypeError, str]:
        """
        Generate or return a TypeError message for an invalid type.

        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [Type Error:] in '[function_name]'
            Description: Unable to complete the [action]. Invalid type for '[attribute_name]' 
            Debug Info: Expected type: '[expected_type],' Received type: '[type(received_value)]'.
            Next Steps: Fix the input or handle the invalid type.
            
        User-Focused Message:
            Unable to complete the [action]. Invalid type for '[attribute_name]' 
            Enter a value of the correct type. *Optional: [suggestion] 
        """
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly
        
        # Context information
        context_stmt = {
            "user": "Invalid type provided.",
            "dev": "TypeError"
        }
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description 
        actual_type_name = received_value if isinstance(received_value, str) else type(received_value).__name__  
        description = {
            'all': f"Unable to {action or 'complete the action'}. Invalid type for '{attribute_name}'(expected {expected_type}, got {actual_type_name})",
        }
        
        # Debugging information
        if not user_friendly:
            debug_info = f"Expected type: '{expected_type}', Received type: '{actual_type_name}'"
        
        # Next steps
        next_step = {
            "user": "Please provide a value of the correct type." if suggestion is None else f"Please provide a value of the correct type.\nSuggestion: {suggestion}",
            "dev": "Fix the input or handle the invalid type."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
            "debug_info": debug_info if not user_friendly else "",
        }
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else TypeError(message)
    
    @staticmethod
    def generate_required_arg_error(
        parameter_name: str,
        action: str = "perform the action",
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = None
    ) -> Union[ValueError, str]:
        """
        Generates an error when a required argument is missing (None).

        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [Value Error:] in '[function_name]'
            Description: Missing required argument '[parameter_name]', cannot be None. 
            Debug Info: 
            Next Steps: Ensure the required argument is provided and not None.
            
        User-Focused Message:
            Cannot [action]. Missing required argument [parameter_name]. 
            Please check the input and try again.
            Suggestion: [suggestion] (if provided)
        """
        
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly
        
        # Context information
        context_stmt = {
            "user": "Missing required argument.",
            "dev": "ValueError"
        }
        
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description
        description = {
            'all': f"Cannot {action}. Missing required argument '{parameter_name}', cannot be None.",
        }
        
        # Next steps
        next_step = {
            "user": f"Please check the input and try again. {f'Suggestion: {suggestion}' if suggestion else ''}",
            "dev": "Ensure the required argument is provided and not None."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
        }
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else ValueError(message)
    
    @staticmethod
    def generate_unexpected_error(
        error_message : str,
        original_exception: Exception,
        action: str = "perform an action",
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = None
        ) -> Union[Exception, str]:
        """
        Generates an Exception with task and context information.

        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [Unexpected Error:] in '[function_name]'
            Description: Unexpected error during [action]: [error_message]
            Debug Info: Original exception: [original_exception]
            Next Steps: Fix the underlying issue or handle the error appropriately.
            
        User-Focused Message:
            An unexpected error occurred while trying to [action]. Please try again or contact support.
            Suggestion: [suggestion] (if provided)
        """
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly

        # Context information
        context_stmt = {
            "user": "Unexpected error.",
            "dev": "UnexpectedError"
        }
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)

        # Description
        description = {
            'all': f"Unexpected error during {action}: {error_message}",
        }
        
        if not user_friendly:
            debug_info = f"Original exception: {original_exception}"

        # Next steps
        next_step = {
            "user": "Please try again or contact support." if suggestion is None else f"Please try again or contact support.\nSuggestion: {suggestion}",
            "dev": "Fix the underlying issue or handle the error appropriately."
        }

        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
            "debug_info": debug_info if not user_friendly else "",
        }
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else Exception(message)
    
    
    @staticmethod
    def generate_permission_error(
        action: str = "access",
        file_path: Union[str, Path, None] = None,
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = "Ensure the file is not currently open and try again."
    ) -> Union[PermissionError, str]:
        """
        Generates a PermissionError message for a file system permission issue.

        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [Permission Error:] in '[function_name]'
            Description: Permission denied to [action] file at '[file_path]'.
            Debug Info: 
            Next Steps: Ensure the necessary file permissions are set correctly.
            
        User-Focused Message:
            Permission denied to [action] file at '[file_path]'.
            Please check the file permissions and try again.
            Suggestion: Ensure the file is not currently open and try again. (if not provided)
        """
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly

        # Context information
        context_stmt = {
            "user": "Permission denied.",
            "dev": "PermissionError"
        }
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)

        # Description
        path_info = f" at '{file_path}'" if file_path else ""
        description = {
            'all': f"Permission denied to {action} the file{path_info}.",
        }
        
        # Next steps
        next_step = {
            "user": f"Please check the file permissions and try again.\n{f'Suggestion: {suggestion}' if suggestion else ''}",
            "dev": "Ensure the necessary file permissions are set correctly."
        }

        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
        }
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else PermissionError(message)
    
    @staticmethod
    def generate_os_error(
        action: str = "access",
        file_path: Union[str, Path, None] = None,
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = "Check disk space or path validity."
        ) -> Union[OSError, str]:
        """
        Generates an OSError message for a file system issue.
        
        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [OS Error:] in '[function_name]'
            Description: Error while trying to [action] file at '[file_path]'.
            Debug Info: 
            Next Steps: Check disk space or path validity.
            
        User-Focused Message:
            Error while trying to [action] file at '[file_path]'.
            Please check the file path and try again.
            Suggestion: Check disk space or path validity. (if not provided)
        """
        
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly
        
        # Context information
        context_stmt = {
            "user": "File system error.",
            "dev": "OSError"
        }
        
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description
        path_info = f" at '{file_path}'" if file_path else ""
        description = {
            'all': f"Error while trying to {action} the file{path_info}.",
        }
        
        # Next steps
        next_step = {
            "user": f"Please check the file path and try again.\n{f'Suggestion: {suggestion}' if suggestion else ''}",
            "dev": "Check disk space or path validity."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
        }
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else OSError(message)
    
    
    @staticmethod
    def generate_file_not_found_error(
        action: str = "perform an action.",
        file_path: Union[str, Path, None] = None,
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = "Ensure the file exists and the path is correct."
    ) -> Union[FileNotFoundError, str]:
        """
        Generates a FileNotFoundError message for a missing file.
        
        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [File Not Found Error:] in '[function_name]'
            Description: Could not [action]. As File not found at '[file_path]'.
            Debug Info: 
            Next Steps: Ensure the file exists and the path is correct.
            
        User-Focused Message:
            Could not [action]. As File not found at '[file_path]'
            Please check the file path and try again.
            Suggestion: Ensure the file exists and the path is correct. (if not provided)
        """
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly

        # Context information
        context_stmt = {
            "user": "File not found.",
            "dev": "FileNotFoundError"
        }
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description
        path_info = f" at '{file_path}'" if file_path else ""
        description = {
            'all': f"Could not {action}. As File not found{path_info}.",
        }
        
        # Next steps
        next_step = {
            "user": f"Please check the file path and try again.\n{f'Suggestion: {suggestion}' if suggestion else ''}",
            "dev": "Ensure the file exists and the path is correct."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
        }
        
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else FileNotFoundError(message)
    
    @staticmethod
    def generate_invalid_list_type_error(
        parameter_name: str, 
        expected_types: str,
        received_values: list,
        action: str = "perform an action",
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = "Check if all elements are of the same type."
    ) -> Union[TypeError, str]:
        """
        Generates a TypeError message for an inconsistent type in a list.
        
        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [Type Error:] in '[function_name]'
            Description: Invalid data type(s) in list '[parameter_name]' during [action].
            Debug Info: Expected types: '[expected_types]', Received values: '[received_values]'.
            Next Steps: Ensure all elements in the list have the correct type.
            
        User-Focused Message:
            Unable to [action]. One or more elements in '[parameter_name]' have an invalid type.
            Please ensure all selected items are one of the following types: [expected_types].
            Suggestion: [suggestion] (if provided)
        """
        
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly
        
        # Context information
        context_stmt = {
            "user": "One or more elements in the list have an invalid type.",
            "dev": "TypeError"
        }
        
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description
        description = {
            'user': f"Unable to {action}. One or more elements in '{parameter_name}' have an invalid type.",
            'dev': f"Invalid data type(s) in list '{parameter_name}' during {action}."
        }
        
        # Debugging information
        debug_info = ""
        if not user_friendly:
            types = [type(val).__name__ for val in received_values]
            debug_info = f"Expected types: '{expected_types}', Received values: '{received_values}(types: {types})'"
            
        # Next steps
        next_step = {
            "user": f"Please ensure all selected items are one of the following types: {expected_types}.\n{f'Suggestion: {suggestion}' if suggestion else ''}",
            "dev": "Ensure all elements in the list have the correct type."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
            "debug_info": debug_info if not user_friendly else "",
        }
        
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else TypeError(message)
        
    @staticmethod
    def generate_empty_list_error(
        parameter_name: str,
        action: str = "perform an action",
        function_name: str = "",
        user_friendly: Optional[bool] = None,
        return_message_only: bool = False,
        suggestion: Optional[str] = "Ensure the list is not empty."
    ) -> Union[ValueError, str]:
        """
        Generates a ValueError message for an empty list.
        
        Developer-Focused Message:
            Context: [YYYY-MMM-DD] [Value Error:] in '[function_name]'
            Description: Empty list '[parameter_name]' provided during [action].
            Debug Info: 
            Next Steps: Ensure the list is not empty.
            
        User-Focused Message:
            Unable to [action]. Empty list '[parameter_name]' provided.
            Please ensure all required items and settings are set and try again.
            Suggestion: [suggestion] (if provided)
        """
            
        user_friendly = ErrorGenerator.DEFAULT_USER_FRIENDLY if user_friendly is None else user_friendly
        
        # Context information
        context_stmt = {
            "user": "Empty list provided.",
            "dev": "ValueError"
        }
        
        context_info = ErrorGenerator._generate_context(context_stmt, function_name, user_friendly)
        
        # Description
        description = {
            'all': f"Unable to {action}. Empty list '{parameter_name}' provided.",
        }
        
        # Next steps
        next_step = {
            "user": f"Please ensure all required items and settings are set and try again.\n{f'Suggestion: {suggestion}' if suggestion else ''}",
            "dev": "Ensure the list is not empty."
        }
        
        # Generate the error message
        template_args = {
            "description": description,
            "next_step": next_step,
            "context_info": context_info,
        }
        
        message = ErrorGenerator._generate_error_message(template_args, user_friendly)
        return message if return_message_only else ValueError(message)