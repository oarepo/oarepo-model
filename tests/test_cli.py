#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the OARepo model CLI commands."""

from __future__ import annotations

import json

from oarepo_model.cli import list_models


def test_model_list(app, cli_runner):
    result = cli_runner(list_models)
    assert result.exit_code == 0
    for _line in """
    datacite_export_test - https://127.0.0.1:5000/api/datacite-export-test -
    test_ui_links        - https://127.0.0.1:5000/api/test-ui-links -
    multilingual_test    - https://127.0.0.1:5000/api/multilingual-test -
    vocabulary_test      - https://127.0.0.1:5000/api/vocabulary-test -
    relation_test        - https://127.0.0.1:5000/api/relation-test -
    drafts_cf            - https://127.0.0.1:5000/api/drafts-cf -
    facet_test           - https://127.0.0.1:5000/api/facet-test -
    records_cf           - https://127.0.0.1:5000/api/records-cf -
    draft_with_files     - https://127.0.0.1:5000/api/draft-with-files -
    draft_test           - https://127.0.0.1:5000/api/draft-test -
    test                 - https://127.0.0.1:5000/api/test -
""".splitlines():
        line = _line.strip()
        if not line:
            continue
        assert line in result.output


def test_dump_marshmallow(app, cli_runner, empty_model):
    """Test dump marshmallow command."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["marshmallow"], None, "test")
    assert result.exit_code == 0
    # Check that output contains schema information
    assert "RecordSchema" in result.output or "class" in result.output


def test_dump_marshmallow_generated(app, cli_runner, empty_model):
    """Test dump marshmallow command with --generated flag."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["marshmallow"], None, "test", "--generated")
    assert result.exit_code == 0


def test_dump_marhsmallow_bad_model(app, cli_runner):
    """Test dump marshmallow command with non-existing model."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["marshmallow"], None, "non_existing_model")
    assert result.exit_code != 0
    assert "Model 'non_existing_model' is not known." in result.output


def test_dump_marhsmallow_bad_model_import(app, cli_runner):
    """Test dump marshmallow command with non-existing model."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["marshmallow"], None, "test.non_existing_model")
    assert result.exit_code != 0
    assert "Model 'test.non_existing_model' cannot be imported." in result.output


def test_dump_ui_marshmallow(app, cli_runner, empty_model):
    """Test dump ui_marshmallow command."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["ui-marshmallow"], None, "test")
    assert result.exit_code == 0
    # Check that output contains schema information
    assert "RecordUISchema" in result.output or "class" in result.output


def test_dump_ui_marshmallow_generated(app, cli_runner, empty_model):
    """Test dump ui_marshmallow command with --generated flag."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["ui-marshmallow"], None, "test", "--generated")
    assert result.exit_code == 0


def test_dump_jsonschema(app, cli_runner, empty_model):
    """Test dump jsonschema command."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["jsonschema"], None, "test")
    assert result.exit_code == 0
    # Verify output is valid JSON
    output = result.output.strip()
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    # Check for typical JSON schema fields
    assert "$schema" in parsed or "properties" in parsed or "type" in parsed


def test_dump_mapping(app, cli_runner, empty_model):
    """Test dump mapping command."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["mapping"], None, "test")
    assert result.exit_code == 0
    # Verify output is valid JSON
    output = result.output.strip()
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    # Check that it contains mapping information
    assert len(parsed) > 0


def test_dump_schema_name_clashes():
    """Test dump_schema handles name clashes correctly."""
    from marshmallow import Schema, fields

    from oarepo_model.cli import dump_schema

    # Create two schemas with the same module and name
    # to simulate a name clash scenario
    class TestSchema(Schema):
        field1 = fields.String()

    # Use the same schema multiple times
    dumped_schemas = set()
    dumped_names = set()
    result = dump_schema(TestSchema, dumped_schemas, dumped_names)

    # First schema should be added
    assert len(result) == 1
    schema_str = next(iter(result.values()))
    assert "class" in schema_str
    assert "field1" in schema_str

    # Now add it again with pre-populated dumped_names to trigger name clash
    original_name = f"{TestSchema.__module__}.{TestSchema.__name__}"
    dumped_names.add(original_name)

    # Create a new schema class with same module and name attributes
    class AnotherTestSchema(Schema):
        field2 = fields.String()

    # Manually set module and name to match
    AnotherTestSchema.__module__ = TestSchema.__module__
    AnotherTestSchema.__name__ = TestSchema.__name__

    dumped_schemas_2 = set()
    result2 = dump_schema(AnotherTestSchema, dumped_schemas_2, dumped_names)

    # Should get a renamed version (with _2 suffix)
    assert len(result2) == 1
    schema_str2 = next(iter(result2.values()))
    assert "_2" in schema_str2
    assert "field2" in schema_str2


def test_dump_schema_field_exception():
    """Test dump_schema handles exceptions in field dumping."""
    from typing import Any

    from marshmallow import Schema, fields

    from oarepo_model.cli import dump_schema

    # Create a field that will cause an exception when dumped
    class ProblematicField(fields.Field):
        """A field that raises an exception during dump."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            # Create an internal attribute that will be used by the property
            self._internal_validate = "placeholder"

        @property
        def validate(self) -> Any:  # type: ignore[override]
            """Property that raises an exception when accessed."""
            raise ValueError("Intentional error for testing")

        @validate.setter
        def validate(self, value: Any) -> None:
            """Setter to allow marshmallow initialization."""
            self._internal_validate = value

    class SchemaWithProblematicField(Schema):
        normal_field = fields.String()
        problematic_field = ProblematicField()

    dumped_schemas = set()
    dumped_names = set()
    result = dump_schema(SchemaWithProblematicField, dumped_schemas, dumped_names)

    # Should still return a result
    assert len(result) == 1
    schema_str = next(iter(result.values()))

    # Normal field should be present
    assert "normal_field" in schema_str

    # Problematic field should have error comment
    assert "problematic_field" in schema_str
    assert "# Error dumping field:" in schema_str
    assert "Intentional error for testing" in schema_str or "Error" in schema_str


def test_dump_schema_nested_schemas():
    """Test dump_schema handles nested schemas correctly."""
    from marshmallow import Schema, fields

    from oarepo_model.cli import dump_schema

    class InnerSchema(Schema):
        inner_field = fields.String()

    class OuterSchema(Schema):
        nested = fields.Nested(InnerSchema)
        normal = fields.String()

    dumped_schemas = set()
    dumped_names = set()
    result = dump_schema(OuterSchema, dumped_schemas, dumped_names)

    # Should dump both outer and inner schemas
    assert len(result) == 2

    # Check that both schemas are in the output
    all_output = "\n".join(result.values())
    assert "OuterSchema" in all_output
    assert "InnerSchema" in all_output
    assert "inner_field" in all_output
    assert "nested" in all_output


def test_dump_field_list():
    """Test dump_field handles List fields correctly."""
    from marshmallow import fields

    from oarepo_model.cli import dump_field

    # Create a List field with String as inner type
    list_field = fields.List(fields.String())

    # Dump the field
    field_str, nested_types = dump_field(list_field)

    # Should contain List and the inner field type
    assert "fields.List" in field_str
    assert "inner=" in field_str
    assert "fields.String" in field_str

    # Should not have nested types for simple fields
    assert len(nested_types) == 0
