#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""OAREPO Model CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast, override

import click
from click import Context, Parameter
from flask.cli import with_appcontext
from invenio_base.utils import obj_or_import_string
from marshmallow import Schema, missing
from marshmallow.fields import Field, List, Nested
from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from types import SimpleNamespace

    from oarepo_runtime.api import Model


class ModelParamType(click.ParamType):
    """Click parameter type for OAREPO models."""

    name = "model"

    @override
    def convert(self, value: Any, param: Parameter | None, ctx: Context | None) -> Any:
        if "." in value:
            try:
                return obj_or_import_string(value)
            except ImportError:
                self.fail(f"Model '{value}' cannot be imported.", param, ctx)

        if value not in current_runtime.models:
            self.fail(f"Model '{value}' is not known.", param, ctx)
        return current_runtime.models[value].namespace


MODEL_TYPE = ModelParamType()


@click.group()
def model() -> None:
    """OAREPO Model commands."""


@model.command(name="list")
@with_appcontext
def list_models() -> None:
    """List known models in the repository."""
    click.secho("\nRDM-like models (/api/records works with them):\n")

    def get_api_url(model: Model) -> str:
        try:
            return str(model.api_url("search"))
        except Exception:  # noqa: BLE001 # in case the url needs some arguments
            return "N/A"

    for model in current_runtime.models.values():
        if model.records_alias_enabled:
            click.echo(f"{model.name!s:20} - {get_api_url(model)} - {model.description}")
    click.secho("\nOther models:\n")
    for model in current_runtime.models.values():
        if not model.records_alias_enabled:
            click.echo(f"{model.name!s:20} - {get_api_url(model)} - {model.description}")


@model.group()
def dump() -> None:
    """Dump various model representations."""


@dump.command()
@click.argument("model", type=MODEL_TYPE)
@click.option("--generated", is_flag=True, help="Dump only generated schemas.")
@with_appcontext
def marshmallow(model: SimpleNamespace, generated: bool) -> None:
    """Dump marshmallow schemas."""
    schema = model.RecordSchema

    for schema_name, schema_str in dump_schema(schema, set(), set()).items():
        if generated and not schema_name.__module__.startswith("oarepo_model.builder"):
            continue
        click.echo(schema_str)
        click.echo("")


@dump.command()
@click.argument("model", type=MODEL_TYPE)
@click.option("--generated", is_flag=True, help="Dump only generated schemas.")
@with_appcontext
def ui_marshmallow(model: SimpleNamespace, generated: bool) -> None:
    """Dump ui marshmallow schemas."""
    schema = model.RecordUISchema

    for schema_name, schema_str in dump_schema(schema, set(), set()).items():
        if generated and not schema_name.__module__.startswith("oarepo_model.builder"):
            continue
        click.echo(schema_str)
        click.echo("")


@dump.command()
@click.argument("model", type=MODEL_TYPE)
@with_appcontext
def jsonschema(model: SimpleNamespace) -> None:
    """Dump JSON schema."""
    click.secho(dump_jsonschema(model))


@dump.command()
@click.argument("model", type=MODEL_TYPE)
@with_appcontext
def mapping(model: SimpleNamespace) -> None:
    """Dump opensearch mapping."""
    click.secho(dump_mapping(model))


def dump_jsonschema(ns: SimpleNamespace) -> str:
    """Dump JSON schema for the model."""
    files = [x for x in ns.__files__ if x.startswith("jsonschemas/") and x.endswith(".json")]
    if not files:
        raise ValueError("No JSON schema files found for this model")
    return cast("str", ns.__files__[files[0]])


def dump_mapping(ns: SimpleNamespace) -> str:
    """Dump mapping for the model."""
    files = {x: json.loads(v) for x, v in ns.__files__.items() if x.startswith("mappings/") and x.endswith(".json")}

    return json.dumps(files, indent=2)


def dump_field(field: Field) -> tuple[str, list[type]]:
    """Dump marshmallow field as string."""
    dumped_field_args: list[str] = []
    nested_types: list[type] = []
    if isinstance(field, Nested):
        subschema: type[Schema] | Schema = field.schema
        if isinstance(subschema, Schema):
            subschema = type(subschema)
        dumped_field_args.append(f'schema="{subschema.__module__}.{subschema.__name__}"')
        nested_types.append(subschema)
    if isinstance(field, List):
        inner_field_str, inner_nested_types = dump_field(field.inner)
        dumped_field_args.append(f"inner={inner_field_str}")
        nested_types.extend(inner_nested_types)

    dump_field_arg(dumped_field_args, field.dump_default, "dump_default")
    dump_field_arg(dumped_field_args, field.attribute, "attribute")
    dump_field_arg(dumped_field_args, field.validate, "validate")
    dump_field_arg(dumped_field_args, field.required, "required")
    dump_field_arg(dumped_field_args, field.load_only, "load_only")
    dump_field_arg(dumped_field_args, field.dump_only, "dump_only")
    dump_field_arg(dumped_field_args, field.load_default, "load_default")
    dump_field_arg(dumped_field_args, field.allow_none, "allow_none")
    return (
        f"fields.{field.__class__.__name__}({', '.join(dumped_field_args)})",
        nested_types,
    )


def dump_field_arg(
    dumped_field_args: list[str],
    field_value: object,
    field_name: str,
) -> None:
    """Dump marshmallow field argument if needed."""
    if isinstance(field_value, bool) and field_value is True:
        dumped_field_args.append(f"{field_name}=True")
    elif field_value is not missing:
        dumped_field_args.append(f"{field_name}={field_value!r}")


def dump_schema(schema: type[Schema] | Schema, dumped_schemas: set[type], dumped_names: set[str]) -> dict[type, str]:
    """Dump marshmallow schema as string."""
    if isinstance(schema, Schema):
        schema = type(schema)

    if not issubclass(schema, Schema):
        raise TypeError("Provided schema is not a marshmallow Schema")  # pragma no cover

    if schema in dumped_schemas:
        return {}
    dumped_schemas.add(schema)

    base_classes = ", \n".join(f"    {base.__module__}.{base.__name__}" for base in schema.__bases__)
    name = f"{schema.__module__}.{schema.__name__}"
    if name in dumped_names:
        # to avoid name clashes, we append a number
        i = 2
        while f"{name}_{i}" in dumped_names:
            i += 1
        name = f"{name}_{i}"
    dumped_names.add(name)
    lines = [f"class {name}(\n{base_classes}\n):"]

    subschemas: set[type] = set()
    for field_name, field_obj in schema._declared_fields.items():  # noqa SLF001
        try:
            dumped_field, other_schemas = dump_field(field_obj)
        except Exception as e:  # noqa: BLE001 # we want to catch all exceptions here
            dumped_field = f"# Error dumping field: {e}"
            other_schemas = []
        lines.append(f"    {field_name} = {dumped_field}")
        subschemas.update([type(t) if isinstance(t, Schema) else t for t in other_schemas])
    ret = {schema: "\n".join(lines)}
    for subschema in subschemas:
        ret.update(dump_schema(subschema, dumped_schemas, dumped_names))

    return ret
