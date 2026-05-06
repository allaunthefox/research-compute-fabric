"""Validators Module.

Input validation utilities for NoDupeLabs.
"""


class ValidationError(Exception):
    """Validation error exception."""


class Validators:
    """Input validation utilities."""

    @staticmethod
    def validate_type(value, expected_type, allow_none=False):
        """Validate that a value is of the expected type.

        Args:
            value: Value to validate
            expected_type: Expected type
            allow_none: Whether None is allowed

        Raises:
            ValidationError: If validation fails
        """
        if allow_none and value is None:
            return True

        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Expected type {expected_type.__name__}, got {type(value).__name__}"
            )
        return True

    @staticmethod
    def validate_range(value, min_val=None, max_val=None, inclusive=True):
        """Validate that a value is within a range.

        Args:
            value: Value to validate
            min_val: Minimum value (None = no minimum)
            max_val: Maximum value (None = no maximum)
            inclusive: Whether range is inclusive

        Raises:
            ValidationError: If validation fails
        """
        if min_val is not None:
            if inclusive and value < min_val:
                raise ValidationError(f"Value {value} is less than minimum {min_val}")
            if not inclusive and value <= min_val:
                raise ValidationError(f"Value {value} must be greater than {min_val}")

        if max_val is not None:
            if inclusive and value > max_val:
                raise ValidationError(f"Value {value} is greater than maximum {max_val}")
            if not inclusive and value >= max_val:
                raise ValidationError(f"Value {value} must be less than {max_val}")

        return True

    @staticmethod
    def validate_not_empty(value, name="Value"):
        """Validate that a value is not empty.

        Args:
            value: Value to validate
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise ValidationError(f"{name} cannot be empty")
        return True

    @staticmethod
    def validate_positive(value, name="Value"):
        """Validate that a numeric value is positive.

        Args:
            value: Value to validate
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if value <= 0:
            raise ValidationError(f"{name} must be positive")
        return True

    @staticmethod
    def validate_non_negative(value, name="Value"):
        """Validate that a numeric value is non-negative.

        Args:
            value: Value to validate
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if value < 0:
            raise ValidationError(f"{name} must be non-negative")
        return True

    @staticmethod
    def validate_string_length(value, min_len=None, max_len=None, name="Value"):
        """Validate that a string is within length bounds.

        Args:
            value: String to validate
            min_len: Minimum length (None = no minimum)
            max_len: Maximum length (None = no maximum)
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"{name} must be a string")

        if min_len is not None and len(value) < min_len:
            raise ValidationError(f"{name} must be at least {min_len} characters")
        if max_len is not None and len(value) > max_len:
            raise ValidationError(f"{name} must be at most {max_len} characters")
        return True

    @staticmethod
    def validate_pattern(value, pattern, name="Value"):
        """Validate that a string matches a regex pattern.

        Args:
            value: String to validate
            pattern: Regex pattern to match
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        import re
        if not isinstance(value, str):
            raise ValidationError(f"{name} must be a string")

        if not re.match(pattern, value):
            raise ValidationError(f"{name} does not match required pattern")
        return True

    @staticmethod
    def validate_email(value, name="Email"):
        """Validate that a string is a valid email address.

        Args:
            value: String to validate
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        import re
        if not isinstance(value, str):
            raise ValidationError(f"{name} must be a string")

        # Simple email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValidationError(f"{name} is not a valid email address")
        return True

    @staticmethod
    def validate_path(value, name="Path", must_exist=False):
        """Validate that a string is a valid path.

        Args:
            value: String to validate
            name: Name of the value for error messages
            must_exist: Whether the path must exist

        Raises:
            ValidationError: If validation fails
        """
        from pathlib import Path
        if not isinstance(value, (str, Path)):
            raise ValidationError(f"{name} must be a path")

        if must_exist and not Path(value).exists():
            raise ValidationError(f"{name} does not exist: {value}")
        return True

    @staticmethod
    def validate_enum(value, allowed_values, name="Value"):
        """Validate that a value is one of the allowed values.

        Args:
            value: Value to validate
            allowed_values: List of allowed values
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if value not in allowed_values:
            raise ValidationError(f"{name} must be one of {allowed_values}")
        return True

    @staticmethod
    def validate_dict_keys(value, required_keys, name="Dict"):
        """Validate that a dict has required keys.

        Args:
            value: Dict to validate
            required_keys: List of required keys
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, dict):
            raise ValidationError(f"{name} must be a dictionary")

        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise ValidationError(f"{name} is missing required keys: {missing_keys}")
        return True

    @staticmethod
    def validate_list_items(value, item_type=None, min_len=None, max_len=None, name="List"):
        """Validate that a list has valid items.

        Args:
            value: List to validate
            item_type: Expected type for each item (None = any type)
            min_len: Minimum length (None = no minimum)
            max_len: Maximum length (None = no maximum)
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, list):
            raise ValidationError(f"{name} must be a list")

        if min_len is not None and len(value) < min_len:
            raise ValidationError(f"{name} must have at least {min_len} items")
        if max_len is not None and len(value) > max_len:
            raise ValidationError(f"{name} must have at most {max_len} items")

        if item_type is not None:
            for i, item in enumerate(value):
                if not isinstance(item, item_type):
                    raise ValidationError(f"{name}[{i}] must be of type {item_type.__name__}")
        return True

    @staticmethod
    def validate_boolean(value, name="Value"):
        """Validate that a value is a boolean.

        Args:
            value: Value to validate
            name: Name of the value for error messages

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, bool):
            raise ValidationError(f"{name} must be a boolean")
        return True
