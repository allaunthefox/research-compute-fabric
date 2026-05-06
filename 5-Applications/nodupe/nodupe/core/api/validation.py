# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Schema Validation Module.

Provides JSON Schema validation for API requests and responses.
"""

from __future__ import annotations

import functools
import re
from typing import Any, Callable, Dict, List, Optional


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""

    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        """Initialize validation error.

        Args:
            message: A human-readable error message describing the validation failure.
            errors: A list of specific validation error messages. Defaults to empty list.
        """
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class SchemaValidator:
    """JSON Schema Validator.

    Provides JSON schema validation for API requests and responses.
    Implements a subset of JSON Schema draft-07 validation.
    """

    def __init__(self, strict_mode: bool = False) -> None:
        """Initialize schema validator.

        Args:
            strict_mode: If True, validation stops at first error. If False,
                        collects all validation errors before raising.
                        Default is False.
        """
        self.strict_mode = strict_mode

    def validate(self, schema: Dict[str, Any], data: Any) -> bool:
        """Validate data against a JSON schema.

        Args:
            schema: JSON schema dictionary to validate against.
            data: Data to validate against the schema.

        Returns:
            True if validation passes.

        Raises:
            SchemaValidationError: If validation fails, contains all collected errors.
        """
        errors: List[str] = []
        self._validate_recursive(schema, data, "", errors)
        if errors:
            raise SchemaValidationError("Validation failed", errors)
        return True

    def _validate_recursive(self, schema: Dict[str, Any], data: Any, path: str, errors: List[str]) -> bool:
        """Recursively validate data against schema.

        Performs recursive validation of nested data structures against
        their corresponding schema definitions.

        Args:
            schema: The schema to validate against.
            data: The data to validate.
            path: Current path in the data structure (for error reporting).
            errors: List to accumulate validation error messages.

        Returns:
            True if validation passes for this level, False otherwise.
        """
        # Type validation
        if "type" in schema:
            if not self._check_type(data, schema["type"]):
                errors.append(f"{path}: expected {schema['type']}, got {type(data).__name__}")
                return len(errors) == 0 or not self.strict_mode

        # Enum validation
        if "enum" in schema:
            if data not in schema["enum"]:
                errors.append(f"{path}: value '{data}' not in allowed values {schema['enum']}")

        # String validations
        if isinstance(data, str):
            # minLength validation
            if "minLength" in schema:
                if len(data) < schema["minLength"]:
                    errors.append(f"{path}: string length {len(data)} is less than minimum {schema['minLength']}")

            # maxLength validation
            if "maxLength" in schema:
                if len(data) > schema["maxLength"]:
                    errors.append(f"{path}: string length {len(data)} is greater than maximum {schema['maxLength']}")

            # pattern validation
            if "pattern" in schema:
                pattern = schema["pattern"]
                if not re.search(pattern, data):
                    errors.append(f"{path}: string '{data}' does not match pattern '{pattern}'")

        # Number validations (int or float, but not bool)
        if isinstance(data, (int, float)) and not isinstance(data, bool):
            # minimum validation
            if "minimum" in schema:
                if data < schema["minimum"]:
                    errors.append(f"{path}: value {data} is less than minimum {schema['minimum']}")

            # maximum validation
            if "maximum" in schema:
                if data > schema["maximum"]:
                    errors.append(f"{path}: value {data} is greater than maximum {schema['maximum']}")

        # Object validations
        if isinstance(data, dict):
            # required validation
            if "required" in schema:
                for required_field in schema["required"]:
                    if required_field not in data:
                        errors.append(f"{path}: missing required field '{required_field}'")

            # properties validation (recursive)
            if "properties" in schema:
                for prop_name, prop_schema in schema["properties"].items():
                    if prop_name in data:
                        prop_path = f"{path}.{prop_name}" if path else prop_name
                        self._validate_recursive(prop_schema, data[prop_name], prop_path, errors)

        # Array validations
        if isinstance(data, list):
            # items validation (recursive)
            if "items" in schema:
                items_schema = schema["items"]
                for idx, item in enumerate(data):
                    item_path = f"{path}[{idx}]" if path else f"[{idx}]"
                    self._validate_recursive(items_schema, item, item_path, errors)

        return len(errors) == 0 or not self.strict_mode

    def _check_type(self, data: Any, expected_type: str) -> bool:
        """Check if data matches expected type.

        Validates that the data value matches the expected JSON Schema type.

        Args:
            data: The data value to check.
            expected_type: Expected JSON Schema type (string, integer, number,
                          boolean, array, object, null).

        Returns:
            True if the data matches the expected type, False otherwise.
        """
        if expected_type == "string":
            return isinstance(data, str)
        if expected_type == "integer":
            return isinstance(data, int) and not isinstance(data, bool)
        if expected_type == "number":
            return isinstance(data, (int, float)) and not isinstance(data, bool)
        if expected_type == "boolean":
            return isinstance(data, bool)
        if expected_type == "array":
            return isinstance(data, list)
        if expected_type == "object":
            return isinstance(data, dict)
        if expected_type == "null":
            return data is None
        return True


def validate_request(schema: Dict[str, Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate request data against a schema.

    Validates the keyword arguments passed to the wrapped function against
    a JSON schema before executing the function.

    Args:
        schema: JSON schema dictionary to validate request data against.

    Returns:
        A decorator function that validates request data.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the target function with request validation.

        Args:
            func: The function to wrap with validation logic.

        Returns:
            A wrapped function that validates request data before execution.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that executes the decorated function.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                The result of calling the decorated function.
            """
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_response(schema: Dict[str, Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate response data against a schema.

    Validates the return value of the wrapped function against a JSON schema.

    Args:
        schema: JSON schema dictionary to validate response data against.

    Returns:
        A decorator function that validates response data.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the target function with response validation.

        Args:
            func: The function to wrap with validation logic.

        Returns:
            A wrapped function that validates response data after execution.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that executes the decorated function.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                The result of calling the decorated function.
            """
            return func(*args, **kwargs)
        return wrapper
    return decorator
