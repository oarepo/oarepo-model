# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for the OARepo model CLI commands."""

from __future__ import annotations

import json

from oarepo_model.cli import list_models


def test_model_list(app, cli_runner, empty_model):
    """Test that a registered RDM-like model is listed with its name and search API URL.

    Only ``empty_model`` is asserted on - other session-scoped models may or may not be
    registered depending on which tests ran first, so they must not be pinned here.
    """
    result = cli_runner(list_models)
    assert result.exit_code == 0
    rdm_section, other_section = result.output.split("Other models:")
    assert "test                 - https://127.0.0.1:5000/api/test - " in rdm_section.splitlines()
    assert "/api/test -" not in other_section


def test_dump_marshmallow(app, cli_runner, empty_model):
    """Test dump marshmallow command dumps the record schema and all nested schemas."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["marshmallow"], None, "test")
    assert result.exit_code == 0
    assert "class runtime_models_test.TestRecordSchema(" in result.output
    assert "class runtime_models_test.TestMetadataSchema(" in result.output
    assert "    title = fields.String(" in result.output


def test_dump_marshmallow_generated(app, cli_runner, empty_model):
    """Test dump marshmallow command with --generated keeps only model-built schemas."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["marshmallow"], None, "test", "--generated")
    assert result.exit_code == 0
    assert "class runtime_models_test.TestRecordSchema(" in result.output
    assert "class runtime_models_test.TestMetadataSchema(" in result.output
    assert "class oarepo_model.presets.records_resources.services.files.record_with_files_schema.FilesSchema(" not in (
        result.output
    )


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
    """Test dump ui_marshmallow command dumps the UI schema and all nested schemas."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["ui-marshmallow"], None, "test")
    assert result.exit_code == 0
    assert "class runtime_models_test.TestRecordUISchema(" in result.output
    # non-generated nested schema is included without --generated
    assert "class invenio_rdm_records.resources.serializers.ui.schema.TombstoneSchema(" in result.output


def test_dump_ui_marshmallow_generated(app, cli_runner, empty_model):
    """Test dump ui_marshmallow command with --generated keeps only model-built schemas."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["ui-marshmallow"], None, "test", "--generated")
    assert result.exit_code == 0
    assert "class runtime_models_test.TestRecordUISchema(" in result.output
    assert "class invenio_rdm_records.resources.serializers.ui.schema.TombstoneSchema(" not in result.output


def test_dump_jsonschema(app, cli_runner, empty_model):
    """Test dump jsonschema command outputs the model's record JSON schema."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["jsonschema"], None, "test")
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert parsed["type"] == "object"
    assert parsed["properties"]["metadata"]["properties"] == {
        "title": {"type": "string"},
        "some_bool_val": {"type": "boolean"},
        "height": {"type": "integer"},
    }


def test_dump_mapping(app, cli_runner, empty_model):
    """Test dump mapping command outputs the model's opensearch mappings keyed by file."""
    from oarepo_model.cli import dump

    result = cli_runner(dump.commands["mapping"], None, "test")
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    mapping = parsed["mappings/os-v2/test/metadata-v1.0.0.json"]["mappings"]
    assert mapping["properties"]["metadata"]["properties"]["height"] == {"type": "integer"}


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
        def validate(self) -> Any:
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
    assert "Intentional error for testing" in schema_str


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
