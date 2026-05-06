# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for the openapi module."""

import json

from nodupe.core.api.openapi import OpenAPIGenerator


class TestOpenAPIGeneratorInitialization:
    """Test OpenAPIGenerator initialization."""

    def test_init(self):
        """Test OpenAPI generator initialization."""
        gen = OpenAPIGenerator()
        assert gen.openapi_version == "3.1.2"
        assert gen.info["title"] == "NoDupeLabs API"
        assert gen.info["version"] == "1.0.0"
        assert gen.info["description"] == "NoDupeLabs API for duplicate file detection"
        assert gen.servers == []
        assert gen.paths == {}
        assert gen.components is not None
        assert "schemas" in gen.components
        assert "responses" in gen.components
        assert "parameters" in gen.components
        assert "securitySchemes" in gen.components
        assert gen.security == []
        assert gen.tags == []


class TestOpenAPIGeneratorSetInfo:
    """Test OpenAPIGenerator set_info method."""

    def test_set_info_basic(self):
        """Test setting API info."""
        gen = OpenAPIGenerator()
        gen.set_info("Test API", "2.0.0", "Test description")
        assert gen.info["title"] == "Test API"
        assert gen.info["version"] == "2.0.0"
        assert gen.info["description"] == "Test description"

    def test_set_info_without_description(self):
        """Test setting API info without description."""
        gen = OpenAPIGenerator()
        gen.set_info("Test API", "2.0.0")
        assert gen.info["title"] == "Test API"
        assert gen.info["version"] == "2.0.0"
        assert "description" not in gen.info

    def test_set_info_returns_self(self):
        """Test set_info returns self for chaining."""
        gen = OpenAPIGenerator()
        result = gen.set_info("Test API", "2.0.0")
        assert result is gen


class TestOpenAPIGeneratorAddServer:
    """Test OpenAPIGenerator add_server method."""

    def test_add_server_basic(self):
        """Test adding server."""
        gen = OpenAPIGenerator()
        gen.add_server("https://api.example.com", "Production")
        assert len(gen.servers) == 1
        assert gen.servers[0]["url"] == "https://api.example.com"
        assert gen.servers[0]["description"] == "Production"

    def test_add_server_without_description(self):
        """Test adding server without description."""
        gen = OpenAPIGenerator()
        gen.add_server("https://api.example.com")
        assert len(gen.servers) == 1
        assert gen.servers[0]["url"] == "https://api.example.com"
        assert "description" not in gen.servers[0]

    def test_add_server_multiple(self):
        """Test adding multiple servers."""
        gen = OpenAPIGenerator()
        gen.add_server("https://api.example.com", "Production")
        gen.add_server("https://staging-api.example.com", "Staging")
        assert len(gen.servers) == 2

    def test_add_server_returns_self(self):
        """Test add_server returns self for chaining."""
        gen = OpenAPIGenerator()
        result = gen.add_server("https://api.example.com")
        assert result is gen


class TestOpenAPIGeneratorAddPath:
    """Test OpenAPIGenerator add_path method."""

    def test_add_path_basic(self):
        """Test adding path."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "get", {"200": {"description": "Success"}})
        assert "/users" in gen.paths
        assert "get" in gen.paths["/users"]
        assert gen.paths["/users"]["get"]["200"]["description"] == "Success"

    def test_add_path_uppercase_method(self):
        """Test adding path with uppercase method."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "GET", {"200": {"description": "Success"}})
        assert "get" in gen.paths["/users"]

    def test_add_path_multiple_methods(self):
        """Test adding multiple methods to same path."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "get", {"200": {"description": "List users"}})
        gen.add_path("/users", "post", {"201": {"description": "Create user"}})
        assert "get" in gen.paths["/users"]
        assert "post" in gen.paths["/users"]

    def test_add_path_multiple_paths(self):
        """Test adding multiple paths."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "get", {})
        gen.add_path("/posts", "get", {})
        assert "/users" in gen.paths
        assert "/posts" in gen.paths

    def test_add_path_returns_self(self):
        """Test add_path returns self for chaining."""
        gen = OpenAPIGenerator()
        result = gen.add_path("/users", "get", {})
        assert result is gen


class TestOpenAPIGeneratorAddSchema:
    """Test OpenAPIGenerator add_schema method."""

    def test_add_schema_basic(self):
        """Test adding schema."""
        gen = OpenAPIGenerator()
        gen.add_schema("User", {"type": "object", "properties": {}})
        assert "User" in gen.components["schemas"]
        assert gen.components["schemas"]["User"]["type"] == "object"

    def test_add_schema_multiple(self):
        """Test adding multiple schemas."""
        gen = OpenAPIGenerator()
        gen.add_schema("User", {"type": "object"})
        gen.add_schema("Post", {"type": "object"})
        assert "User" in gen.components["schemas"]
        assert "Post" in gen.components["schemas"]

    def test_add_schema_complex(self):
        """Test adding complex schema."""
        gen = OpenAPIGenerator()
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["id", "name"]
        }
        gen.add_schema("User", schema)
        assert gen.components["schemas"]["User"] == schema

    def test_add_schema_returns_self(self):
        """Test add_schema returns self for chaining."""
        gen = OpenAPIGenerator()
        result = gen.add_schema("User", {"type": "object"})
        assert result is gen


class TestOpenAPIGeneratorGenerateSpec:
    """Test OpenAPIGenerator generate_spec method."""

    def test_generate_spec_basic(self):
        """Test generating spec."""
        gen = OpenAPIGenerator()
        spec = gen.generate_spec()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert spec["openapi"] == "3.1.2"

    def test_generate_spec_with_servers(self):
        """Test generating spec with servers."""
        gen = OpenAPIGenerator()
        gen.add_server("https://api.example.com")
        spec = gen.generate_spec()
        assert "servers" in spec
        assert len(spec["servers"]) == 1

    def test_generate_spec_with_paths(self):
        """Test generating spec with paths."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "get", {"200": {"description": "Success"}})
        spec = gen.generate_spec()
        assert "/users" in spec["paths"]

    def test_generate_spec_with_components(self):
        """Test generating spec with components."""
        gen = OpenAPIGenerator()
        gen.add_schema("User", {"type": "object"})
        spec = gen.generate_spec()
        assert "components" in spec
        assert "schemas" in spec["components"]
        assert "User" in spec["components"]["schemas"]

    def test_generate_spec_without_empty_components(self):
        """Test generating spec doesn't include empty components."""
        gen = OpenAPIGenerator()
        spec = gen.generate_spec()
        # Empty components should not be included
        assert "components" not in spec or not any(spec.get("components", {}).values())


class TestOpenAPIGeneratorToJson:
    """Test OpenAPIGenerator to_json method."""

    def test_to_json_basic(self):
        """Test converting to JSON."""
        gen = OpenAPIGenerator()
        json_str = gen.to_json()
        assert isinstance(json_str, str)
        spec = json.loads(json_str)
        assert "openapi" in spec

    def test_to_json_with_spec(self):
        """Test converting custom spec to JSON."""
        gen = OpenAPIGenerator()
        custom_spec = {"openapi": "3.1.2", "info": {"title": "Test"}, "paths": {}}
        json_str = gen.to_json(custom_spec)
        parsed = json.loads(json_str)
        assert parsed["info"]["title"] == "Test"

    def test_to_json_indent(self):
        """Test converting to JSON with custom indent."""
        gen = OpenAPIGenerator()
        json_str = gen.to_json(indent=4)
        # Should have 4-space indentation
        assert "    " in json_str

    def test_to_json_compact(self):
        """Test converting to JSON with no indent."""
        gen = OpenAPIGenerator()
        json_str = gen.to_json(indent=None)  # Use None for compact
        # With indent=None, json.dumps produces compact output
        parsed = json.loads(json_str)
        assert "openapi" in parsed


class TestOpenAPIGeneratorValidateSpec:
    """Test OpenAPIGenerator validate_spec method."""

    def test_validate_spec_valid(self):
        """Test validating valid spec."""
        gen = OpenAPIGenerator()
        result = gen.validate_spec()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_spec_missing_openapi(self):
        """Test validating spec missing openapi field."""
        gen = OpenAPIGenerator()
        invalid_spec = {"info": {"title": "Test"}, "paths": {}}
        result = gen.validate_spec(invalid_spec)
        assert result["valid"] is False
        assert "openapi" in str(result["errors"])

    def test_validate_spec_missing_info(self):
        """Test validating spec missing info field."""
        gen = OpenAPIGenerator()
        invalid_spec = {"openapi": "3.1.2", "paths": {}}
        result = gen.validate_spec(invalid_spec)
        assert result["valid"] is False
        assert "info" in str(result["errors"])

    def test_validate_spec_missing_paths(self):
        """Test validating spec missing paths field."""
        gen = OpenAPIGenerator()
        invalid_spec = {"openapi": "3.1.2", "info": {"title": "Test"}}
        result = gen.validate_spec(invalid_spec)
        assert result["valid"] is False
        assert "paths" in str(result["errors"])

    def test_validate_spec_multiple_errors(self):
        """Test validating spec with multiple errors."""
        gen = OpenAPIGenerator()
        invalid_spec = {}
        result = gen.validate_spec(invalid_spec)
        assert result["valid"] is False
        assert len(result["errors"]) >= 3  # openapi, info, paths


class TestOpenAPIGeneratorMethodChaining:
    """Test OpenAPIGenerator method chaining."""

    def test_chain_set_info_add_server(self):
        """Test chaining set_info and add_server."""
        gen = OpenAPIGenerator()
        gen.set_info("Test API", "1.0.0").add_server("https://api.example.com")
        assert gen.info["title"] == "Test API"
        assert len(gen.servers) == 1

    def test_chain_add_path_add_schema(self):
        """Test chaining add_path and add_schema."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "get", {}).add_schema("User", {"type": "object"})
        assert "/users" in gen.paths
        assert "User" in gen.components["schemas"]

    def test_chain_full_workflow(self):
        """Test complete workflow with chaining."""
        gen = OpenAPIGenerator()
        gen.set_info("Test API", "1.0.0", "Test") \
           .add_server("https://api.example.com") \
           .add_path("/users", "get", {"200": {"description": "List users"}}) \
           .add_schema("User", {"type": "object"})

        spec = gen.generate_spec()
        assert spec["openapi"] == "3.1.2"
        assert spec["info"]["title"] == "Test API"
        assert len(spec["servers"]) == 1
        assert "/users" in spec["paths"]
        assert "User" in spec["components"]["schemas"]


class TestOpenAPIGeneratorEdgeCases:
    """Test OpenAPIGenerator edge cases."""

    def test_add_path_empty_operation(self):
        """Test adding path with empty operation."""
        gen = OpenAPIGenerator()
        gen.add_path("/test", "get", {})
        assert "/test" in gen.paths
        assert gen.paths["/test"]["get"] == {}

    def test_add_schema_empty_schema(self):
        """Test adding empty schema."""
        gen = OpenAPIGenerator()
        gen.add_schema("Empty", {})
        assert gen.components["schemas"]["Empty"] == {}

    def test_generate_spec_empty(self):
        """Test generating spec with no additions."""
        gen = OpenAPIGenerator()
        spec = gen.generate_spec()
        assert spec["paths"] == {}
        assert spec["info"]["title"] == "NoDupeLabs API"

    def test_validate_spec_with_none(self):
        """Test validate_spec with None uses generated spec."""
        gen = OpenAPIGenerator()
        result = gen.validate_spec(None)
        assert result["valid"] is True
