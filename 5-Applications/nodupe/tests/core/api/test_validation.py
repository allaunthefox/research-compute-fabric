# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for the validation module."""

import pytest

from nodupe.core.api.validation import (
    SchemaValidationError,
    SchemaValidator,
    validate_request,
    validate_response,
)


class TestSchemaValidationError:
    """Test SchemaValidationError exception."""

    def test_exception_basic(self):
        """Test basic exception creation."""
        exc = SchemaValidationError("Validation failed")
        assert exc.message == "Validation failed"
        assert exc.errors == []
        assert str(exc) == "Validation failed"

    def test_exception_with_errors(self):
        """Test exception with errors list."""
        errors = ["Field 'name' is required", "Field 'age' must be integer"]
        exc = SchemaValidationError("Validation failed", errors)
        assert exc.message == "Validation failed"
        assert exc.errors == errors
        assert str(exc) == "Validation failed"

    def test_exception_inheritance(self):
        """Test exception inherits from Exception."""
        exc = SchemaValidationError("Validation failed")
        assert isinstance(exc, Exception)


class TestSchemaValidatorInitialization:
    """Test SchemaValidator initialization."""

    def test_init_default(self):
        """Test validator initialization with default values."""
        validator = SchemaValidator()
        assert validator.strict_mode is False

    def test_init_strict_mode(self):
        """Test validator initialization with strict mode."""
        validator = SchemaValidator(strict_mode=True)
        assert validator.strict_mode is True


class TestSchemaValidatorValidate:
    """Test SchemaValidator validate method."""

    def test_validate_string_valid(self):
        """Test validating valid string."""
        validator = SchemaValidator()
        result = validator.validate({"type": "string"}, "hello")
        assert result is True

    def test_validate_string_invalid(self):
        """Test validating invalid string raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "string"}, 42)

    def test_validate_integer_valid(self):
        """Test validating valid integer."""
        validator = SchemaValidator()
        result = validator.validate({"type": "integer"}, 42)
        assert result is True

    def test_validate_integer_invalid_string(self):
        """Test validating integer with string raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "integer"}, "42")

    def test_validate_integer_invalid_float(self):
        """Test validating integer with float raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "integer"}, 42.5)

    def test_validate_integer_bool_not_allowed(self):
        """Test that bool is not considered integer."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "integer"}, True)

    def test_validate_number_int_valid(self):
        """Test validating number with int."""
        validator = SchemaValidator()
        result = validator.validate({"type": "number"}, 42)
        assert result is True

    def test_validate_number_float_valid(self):
        """Test validating number with float."""
        validator = SchemaValidator()
        result = validator.validate({"type": "number"}, 42.5)
        assert result is True

    def test_validate_number_invalid(self):
        """Test validating number with string raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "number"}, "42")

    def test_validate_boolean_valid(self):
        """Test validating valid boolean."""
        validator = SchemaValidator()
        result = validator.validate({"type": "boolean"}, True)
        assert result is True

        result = validator.validate({"type": "boolean"}, False)
        assert result is True

    def test_validate_boolean_invalid(self):
        """Test validating invalid boolean raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "boolean"}, 1)

    def test_validate_array_valid(self):
        """Test validating valid array."""
        validator = SchemaValidator()
        result = validator.validate({"type": "array"}, [1, 2, 3])
        assert result is True

    def test_validate_array_invalid(self):
        """Test validating invalid array raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "array"}, "not an array")

    def test_validate_object_valid(self):
        """Test validating valid object."""
        validator = SchemaValidator()
        result = validator.validate({"type": "object"}, {"key": "value"})
        assert result is True

    def test_validate_object_invalid(self):
        """Test validating invalid object raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "object"}, "not an object")

    def test_validate_null_valid(self):
        """Test validating valid null."""
        validator = SchemaValidator()
        result = validator.validate({"type": "null"}, None)
        assert result is True

    def test_validate_null_invalid(self):
        """Test validating invalid null raises error."""
        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "null"}, "not null")

    def test_validate_unknown_type(self):
        """Test validating with unknown type passes (no validation)."""
        validator = SchemaValidator()
        result = validator.validate({"type": "unknown_type"}, "any value")
        # Unknown types pass through without validation
        assert result is True

    def test_validate_no_type(self):
        """Test validating schema without type."""
        validator = SchemaValidator()
        result = validator.validate({}, "any value")
        # No type means no validation
        assert result is True

    def test_validate_strict_mode_error(self):
        """Test strict mode raises on validation error."""
        validator = SchemaValidator(strict_mode=True)
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "string"}, 42)

    def test_validate_non_strict_mode(self):
        """Test non-strict mode behavior."""
        validator = SchemaValidator(strict_mode=False)
        # In non-strict mode, validation still raises errors
        with pytest.raises(SchemaValidationError):
            validator.validate({"type": "string"}, 42)


class TestSchemaValidatorValidateRecursive:
    """Test SchemaValidator _validate_recursive method."""

    def test_validate_recursive_type_check(self):
        """Test recursive validation type checking."""
        validator = SchemaValidator()
        errors = []
        result = validator._validate_recursive(
            {"type": "string"},
            "hello",
            "",
            errors
        )
        assert result is True
        assert errors == []

    def test_validate_recursive_type_mismatch(self):
        """Test recursive validation type mismatch."""
        validator = SchemaValidator()
        errors = []
        result = validator._validate_recursive(
            {"type": "string"},
            42,
            "field",
            errors
        )
        # In non-strict mode, returns True even with errors
        assert result is True
        assert len(errors) == 1
        assert "expected string" in errors[0]

    def test_validate_recursive_with_path(self):
        """Test recursive validation includes path in error."""
        validator = SchemaValidator()
        errors = []
        validator._validate_recursive(
            {"type": "integer"},
            "not an int",
            "user.age",
            errors
        )
        assert len(errors) == 1
        assert "user.age" in errors[0]


class TestSchemaValidatorCheckType:
    """Test SchemaValidator _check_type method."""

    def test_check_type_string(self):
        """Test check_type for string."""
        validator = SchemaValidator()
        assert validator._check_type("hello", "string") is True
        assert validator._check_type(42, "string") is False

    def test_check_type_integer(self):
        """Test check_type for integer."""
        validator = SchemaValidator()
        assert validator._check_type(42, "integer") is True
        assert validator._check_type(42.5, "integer") is False
        assert validator._check_type("42", "integer") is False

    def test_check_type_integer_bool_excluded(self):
        """Test check_type excludes bool from integer."""
        validator = SchemaValidator()
        assert validator._check_type(True, "integer") is False
        assert validator._check_type(False, "integer") is False

    def test_check_type_number(self):
        """Test check_type for number."""
        validator = SchemaValidator()
        assert validator._check_type(42, "number") is True
        assert validator._check_type(42.5, "number") is True
        assert validator._check_type("42", "number") is False

    def test_check_type_number_bool_excluded(self):
        """Test check_type excludes bool from number."""
        validator = SchemaValidator()
        assert validator._check_type(True, "number") is False

    def test_check_type_boolean(self):
        """Test check_type for boolean."""
        validator = SchemaValidator()
        assert validator._check_type(True, "boolean") is True
        assert validator._check_type(False, "boolean") is True
        assert validator._check_type(1, "boolean") is False

    def test_check_type_array(self):
        """Test check_type for array."""
        validator = SchemaValidator()
        assert validator._check_type([1, 2, 3], "array") is True
        assert validator._check_type("not array", "array") is False

    def test_check_type_object(self):
        """Test check_type for object."""
        validator = SchemaValidator()
        assert validator._check_type({"key": "value"}, "object") is True
        assert validator._check_type("not object", "object") is False

    def test_check_type_null(self):
        """Test check_type for null."""
        validator = SchemaValidator()
        assert validator._check_type(None, "null") is True
        assert validator._check_type("not null", "null") is False

    def test_check_type_unknown(self):
        """Test check_type for unknown type."""
        validator = SchemaValidator()
        assert validator._check_type("any", "unknown_type") is True


class TestValidateRequestDecorator:
    """Test validate_request decorator."""

    def test_decorator_basic(self):
        """Test basic decorator functionality."""
        @validate_request({"type": "object"})
        def test_func(data):
            """Test function for validate_request decorator."""
            return data

        result = test_func({"key": "value"})
        assert result == {"key": "value"}

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves function name."""
        @validate_request({"type": "object"})
        def my_validated_function(data):
            """Validated function for decorator name test."""
            return data

        assert my_validated_function.__name__ == "my_validated_function"

    def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @validate_request({"type": "object"})
        def test_func(a, b):
            """Test function with positional arguments."""
            return a + b

        result = test_func(1, 2)
        assert result == 3

    def test_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""
        @validate_request({"type": "object"})
        def test_func(a, b=10):
            """Test function with keyword arguments."""
            return a + b

        result = test_func(1, b=20)
        assert result == 21


class TestValidateResponseDecorator:
    """Test validate_response decorator."""

    def test_decorator_basic(self):
        """Test basic decorator functionality."""
        @validate_response({"type": "object"})
        def test_func():
            """Test function for validate_response decorator."""
            return {"result": "success"}

        result = test_func()
        assert result == {"result": "success"}

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves function name."""
        @validate_response({"type": "object"})
        def my_validated_response_function():
            """Validated response function for name test."""
            return {"result": "success"}

        assert my_validated_response_function.__name__ == "my_validated_response_function"

    def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @validate_response({"type": "object"})
        def test_func(a, b):
            """Test function with positional arguments."""
            return {"sum": a + b}

        result = test_func(1, 2)
        assert result == {"sum": 3}


class TestValidationIntegration:
    """Test validation integration scenarios."""

    def test_complete_validation_workflow(self):
        """Test complete validation workflow."""
        validator = SchemaValidator()

        # Valid data
        schema = {"type": "object"}
        data = {"name": "test", "value": 123}
        result = validator.validate(schema, data)
        assert result is True

        # Invalid data
        invalid_data = "not an object"
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, invalid_data)

    def test_complex_schema_validation(self):
        """Test complex schema validation."""
        validator = SchemaValidator()

        # Test multiple type validations
        assert validator.validate({"type": "string"}, "hello") is True
        assert validator.validate({"type": "integer"}, 42) is True
        assert validator.validate({"type": "number"}, 3.14) is True
        assert validator.validate({"type": "boolean"}, True) is True
        assert validator.validate({"type": "array"}, [1, 2, 3]) is True
        assert validator.validate({"type": "object"}, {}) is True
        assert validator.validate({"type": "null"}, None) is True

    def test_error_collection(self):
        """Test error collection in validation."""
        validator = SchemaValidator()

        try:
            validator.validate({"type": "string"}, 42)
        except SchemaValidationError as e:
            assert len(e.errors) >= 1
            assert "expected string" in e.errors[0]


class TestValidationEdgeCases:
    """Test validation edge cases."""

    def test_validate_empty_string(self):
        """Test validating empty string."""
        validator = SchemaValidator()
        result = validator.validate({"type": "string"}, "")
        assert result is True

    def test_validate_zero(self):
        """Test validating zero."""
        validator = SchemaValidator()
        result = validator.validate({"type": "integer"}, 0)
        assert result is True

    def test_validate_empty_array(self):
        """Test validating empty array."""
        validator = SchemaValidator()
        result = validator.validate({"type": "array"}, [])
        assert result is True

    def test_validate_empty_object(self):
        """Test validating empty object."""
        validator = SchemaValidator()
        result = validator.validate({"type": "object"}, {})
        assert result is True

    def test_validate_nested_object(self):
        """Test validating nested object (type only)."""
        validator = SchemaValidator()
        nested = {"outer": {"inner": {"deep": "value"}}}
        result = validator.validate({"type": "object"}, nested)
        assert result is True

    def test_validate_large_array(self):
        """Test validating large array."""
        validator = SchemaValidator()
        large_array = list(range(10000))
        result = validator.validate({"type": "array"}, large_array)
        assert result is True


class TestSchemaValidatorRequiredFields:
    """Test required fields validation."""

    def test_required_fields_valid(self):
        """Test validation with all required fields present."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "age"]
        }
        data = {"name": "John", "age": 30}
        result = validator.validate(schema, data)
        assert result is True

    def test_required_fields_missing_one(self):
        """Test validation with one required field missing."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "age"]
        }
        data = {"name": "John"}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, data)
        assert "missing required field 'age'" in str(exc_info.value.errors)

    def test_required_fields_missing_multiple(self):
        """Test validation with multiple required fields missing."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "age", "email"]
        }
        data = {}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, data)
        errors = exc_info.value.errors
        assert len(errors) == 3
        assert any("missing required field 'name'" in e for e in errors)
        assert any("missing required field 'age'" in e for e in errors)
        assert any("missing required field 'email'" in e for e in errors)

    def test_required_fields_non_object_ignored(self):
        """Test that required is ignored for non-object types."""
        validator = SchemaValidator()
        schema = {
            "type": "string",
            "required": ["name"]
        }
        data = "hello"
        result = validator.validate(schema, data)
        assert result is True


class TestSchemaValidatorStringLength:
    """Test string length validation (minLength/maxLength)."""

    def test_min_length_valid(self):
        """Test validation with string meeting minimum length."""
        validator = SchemaValidator()
        schema = {"type": "string", "minLength": 3}
        result = validator.validate(schema, "hello")
        assert result is True

    def test_min_length_exact(self):
        """Test validation with string at exact minimum length."""
        validator = SchemaValidator()
        schema = {"type": "string", "minLength": 5}
        result = validator.validate(schema, "hello")
        assert result is True

    def test_min_length_violation(self):
        """Test validation with string below minimum length."""
        validator = SchemaValidator()
        schema = {"type": "string", "minLength": 5}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, "hi")
        assert "less than minimum" in str(exc_info.value.errors[0])

    def test_max_length_valid(self):
        """Test validation with string within maximum length."""
        validator = SchemaValidator()
        schema = {"type": "string", "maxLength": 10}
        result = validator.validate(schema, "hello")
        assert result is True

    def test_max_length_exact(self):
        """Test validation with string at exact maximum length."""
        validator = SchemaValidator()
        schema = {"type": "string", "maxLength": 5}
        result = validator.validate(schema, "hello")
        assert result is True

    def test_max_length_violation(self):
        """Test validation with string exceeding maximum length."""
        validator = SchemaValidator()
        schema = {"type": "string", "maxLength": 5}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, "hello world")
        assert "greater than maximum" in str(exc_info.value.errors[0])

    def test_min_max_length_combined(self):
        """Test validation with both minLength and maxLength."""
        validator = SchemaValidator()
        schema = {"type": "string", "minLength": 3, "maxLength": 5}

        # Valid
        assert validator.validate(schema, "hello") is True
        assert validator.validate(schema, "abc") is True

        # Too short
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "ab")

        # Too long
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "hello!")


class TestSchemaValidatorNumberRange:
    """Test number range validation (minimum/maximum)."""

    def test_minimum_valid(self):
        """Test validation with number meeting minimum."""
        validator = SchemaValidator()
        schema = {"type": "number", "minimum": 0}
        result = validator.validate(schema, 10)
        assert result is True

    def test_minimum_exact(self):
        """Test validation with number at exact minimum."""
        validator = SchemaValidator()
        schema = {"type": "number", "minimum": 0}
        result = validator.validate(schema, 0)
        assert result is True

    def test_minimum_violation(self):
        """Test validation with number below minimum."""
        validator = SchemaValidator()
        schema = {"type": "number", "minimum": 0}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, -5)
        assert "less than minimum" in str(exc_info.value.errors[0])

    def test_maximum_valid(self):
        """Test validation with number within maximum."""
        validator = SchemaValidator()
        schema = {"type": "number", "maximum": 100}
        result = validator.validate(schema, 50)
        assert result is True

    def test_maximum_exact(self):
        """Test validation with number at exact maximum."""
        validator = SchemaValidator()
        schema = {"type": "number", "maximum": 100}
        result = validator.validate(schema, 100)
        assert result is True

    def test_maximum_violation(self):
        """Test validation with number exceeding maximum."""
        validator = SchemaValidator()
        schema = {"type": "number", "maximum": 100}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, 150)
        assert "greater than maximum" in str(exc_info.value.errors[0])

    def test_minimum_maximum_combined(self):
        """Test validation with both minimum and maximum."""
        validator = SchemaValidator()
        schema = {"type": "number", "minimum": 0, "maximum": 100}

        # Valid
        assert validator.validate(schema, 50) is True
        assert validator.validate(schema, 0) is True
        assert validator.validate(schema, 100) is True

        # Too low
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, -1)

        # Too high
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, 101)

    def test_minimum_maximum_integer(self):
        """Test minimum/maximum with integer type."""
        validator = SchemaValidator()
        schema = {"type": "integer", "minimum": 1, "maximum": 10}

        # Valid
        assert validator.validate(schema, 5) is True

        # Too low
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, 0)

        # Too high
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, 11)


class TestSchemaValidatorPattern:
    """Test string pattern validation."""

    def test_pattern_valid(self):
        """Test validation with string matching pattern."""
        validator = SchemaValidator()
        schema = {"type": "string", "pattern": "^[a-z]+$"}
        result = validator.validate(schema, "hello")
        assert result is True

    def test_pattern_violation(self):
        """Test validation with string not matching pattern."""
        validator = SchemaValidator()
        schema = {"type": "string", "pattern": "^[a-z]+$"}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, "Hello123")
        assert "does not match pattern" in str(exc_info.value.errors[0])

    def test_pattern_email(self):
        """Test validation with email pattern."""
        validator = SchemaValidator()
        schema = {"type": "string", "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"}

        # Valid email
        assert validator.validate(schema, "test@example.com") is True

        # Invalid email
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "not-an-email")

    def test_pattern_phone(self):
        """Test validation with phone pattern."""
        validator = SchemaValidator()
        schema = {"type": "string", "pattern": "^\\d{3}-\\d{3}-\\d{4}$"}

        # Valid phone
        assert validator.validate(schema, "123-456-7890") is True

        # Invalid phone
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "1234567890")


class TestSchemaValidatorEnum:
    """Test enum validation."""

    def test_enum_valid(self):
        """Test validation with value in enum."""
        validator = SchemaValidator()
        schema = {"type": "string", "enum": ["red", "green", "blue"]}
        result = validator.validate(schema, "red")
        assert result is True

    def test_enum_violation(self):
        """Test validation with value not in enum."""
        validator = SchemaValidator()
        schema = {"type": "string", "enum": ["red", "green", "blue"]}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, "yellow")
        assert "not in allowed values" in str(exc_info.value.errors[0])

    def test_enum_integer(self):
        """Test enum with integer values."""
        validator = SchemaValidator()
        schema = {"type": "integer", "enum": [1, 2, 3]}

        # Valid
        assert validator.validate(schema, 2) is True

        # Invalid
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, 4)

    def test_enum_mixed_types(self):
        """Test enum with mixed type values."""
        validator = SchemaValidator()
        schema = {"enum": [1, "one", True, None]}

        assert validator.validate(schema, 1) is True
        assert validator.validate(schema, "one") is True
        assert validator.validate(schema, True) is True
        assert validator.validate(schema, None) is True
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, 2)


class TestSchemaValidatorProperties:
    """Test object properties validation."""

    def test_properties_valid(self):
        """Test validation with valid object properties."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        data = {"name": "John", "age": 30}
        result = validator.validate(schema, data)
        assert result is True

    def test_properties_invalid_value(self):
        """Test validation with invalid property value."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        data = {"name": "John", "age": "thirty"}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, data)
        assert "age" in str(exc_info.value.errors[0])
        assert "expected integer" in str(exc_info.value.errors[0])

    def test_properties_nested(self):
        """Test validation with nested object properties."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            }
        }
        data = {"user": {"name": "John", "email": "john@example.com"}}
        result = validator.validate(schema, data)
        assert result is True

    def test_properties_nested_invalid(self):
        """Test validation with nested object invalid property."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    }
                }
            }
        }
        data = {"user": {"name": "John", "age": "not a number"}}
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, data)
        errors_str = str(exc_info.value.errors)
        assert "user.age" in errors_str


class TestSchemaValidatorArrayItems:
    """Test array items validation."""

    def test_items_valid(self):
        """Test validation with valid array items."""
        validator = SchemaValidator()
        schema = {
            "type": "array",
            "items": {"type": "integer"}
        }
        data = [1, 2, 3, 4, 5]
        result = validator.validate(schema, data)
        assert result is True

    def test_items_invalid(self):
        """Test validation with invalid array item."""
        validator = SchemaValidator()
        schema = {
            "type": "array",
            "items": {"type": "integer"}
        }
        data = [1, 2, "three", 4]
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, data)
        assert "[2]" in str(exc_info.value.errors[0])
        assert "expected integer" in str(exc_info.value.errors[0])

    def test_items_nested_objects(self):
        """Test validation with array of nested objects."""
        validator = SchemaValidator()
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            }
        }
        data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]
        result = validator.validate(schema, data)
        assert result is True

    def test_items_nested_objects_invalid(self):
        """Test validation with array of invalid nested objects."""
        validator = SchemaValidator()
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                }
            }
        }
        data = [
            {"id": 1},
            {"id": "not an integer"}
        ]
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, data)
        assert "[1].id" in str(exc_info.value.errors[0])


class TestSchemaValidatorCombinedConstraints:
    """Test combined validation constraints."""

    def test_required_with_properties(self):
        """Test required fields combined with properties validation."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "email": {"type": "string", "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150}
            }
        }

        # Valid
        data = {"name": "John", "email": "john@example.com", "age": 30}
        assert validator.validate(schema, data) is True

        # Missing required
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(schema, {"name": "John"})
        assert "missing required field 'email'" in str(exc_info.value.errors[0])

        # Invalid property type
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, {"name": "John", "email": "john@example.com", "age": -5})

    def test_string_all_constraints(self):
        """Test string with all constraints."""
        validator = SchemaValidator()
        schema = {
            "type": "string",
            "minLength": 3,
            "maxLength": 10,
            "pattern": "^[a-z]+$",
            "enum": ["hello", "world", "foo", "bar"]
        }

        # Valid
        assert validator.validate(schema, "hello") is True
        assert validator.validate(schema, "foo") is True

        # Too short
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "ab")

        # Too long
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "hellooooo")

        # Wrong pattern
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "HELLO")

        # Not in enum
        with pytest.raises(SchemaValidationError):
            validator.validate(schema, "baz")


class TestToolRegistryImportFix:
    """Test that tool registry imports work correctly after fix."""

    def test_tool_registry_imports(self):
        """Test that tool registry can import ActionCode and AccessibleTool."""
        # This test verifies the import paths are correct
        from nodupe.core.api.codes import ActionCode
        from nodupe.core.tool_system.base import AccessibleTool, Tool

        # Verify imports succeeded
        assert ActionCode is not None
        assert AccessibleTool is not None
        assert Tool is not None

        # Verify AccessibleTool is a subclass of Tool
        assert issubclass(AccessibleTool, Tool)

    def test_tool_registry_registration_with_accessible_tool(self):
        """Test that tool registration works with correct imports."""
        from nodupe.core.tool_system.base import AccessibleTool
        from nodupe.core.tool_system.registry import ToolRegistry

        # Reset singleton
        ToolRegistry._reset_instance()

        registry = ToolRegistry()

        # Create a mock accessible tool
        class TestAccessibleTool(AccessibleTool):
            """Mock AccessibleTool for testing."""
            @property
            def name(self) -> str:
                """Return tool name."""
                return "TestAccessibleTool"

            @property
            def version(self) -> str:
                """Return tool version."""
                return "1.0.0"

            @property
            def dependencies(self):
                """Return tool dependencies."""
                return []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Return tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """Return API methods."""
                return {}

            def run_standalone(self, args):
                """Run tool standalone."""
                return 0

            def describe_usage(self):
                """Describe tool usage."""
                return "Test tool"

        tool = TestAccessibleTool()

        # This should not raise an import error
        registry.register(tool)

        # Verify tool was registered
        assert registry.get_tool("TestAccessibleTool") is not None

        # Cleanup
        ToolRegistry._reset_instance()

    def test_tool_registry_registration_basic(self):
        """Test basic tool registration works after import fix."""
        from unittest.mock import Mock

        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.registry import ToolRegistry

        # Reset singleton
        ToolRegistry._reset_instance()

        registry = ToolRegistry()

        mock_tool = Mock(spec=Tool)
        mock_tool.name = "BasicTool"
        mock_tool.initialize = Mock()
        mock_tool.shutdown = Mock()

        # This should not raise an import error
        registry.register(mock_tool)

        # Verify tool was registered
        assert registry.get_tool("BasicTool") is mock_tool

        # Cleanup
        ToolRegistry._reset_instance()
