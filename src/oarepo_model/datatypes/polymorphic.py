# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Polymorphic data type: ``polymorphic``, a value that is one of several variants.

The ``discriminator`` property (default ``type``) names the field whose value selects
the variant from ``oneof``. Each variant has a ``discriminator`` value and a ``type``:
an ``object`` with inline properties, or the name of a type defined elsewhere in the
model. A value with a missing or unknown discriminator is rejected.

Every variant must itself declare the discriminator field (e.g. as a ``keyword``).
Otherwise loading fails with ``Unknown field.``, even though the JSON schema and
the mapping add it automatically.

In the search index all variants share one object mapping with the union of their
properties. No facets are generated.

Example (model YAML):

```yaml
creator:
  type: polymorphic
  discriminator: creator_type
  oneof:
    - discriminator: person
      type: object
      properties:
        creator_type:
          type: keyword
        name:
          type: fulltext+keyword
        orcid:
          type: keyword
    - discriminator: organization
      type: object
      properties:
        creator_type:
          type: keyword
        name:
          type: fulltext+keyword
        ror_id:
          type: keyword
```

See https://nrp-cz.github.io/docs/customize/model_backend/model_reference#polymorphic
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from invenio_base.utils import obj_or_import_string
from marshmallow.utils import get_value
from marshmallow.utils import (
    missing as missing_,
)

from oarepo_model.utils import readonly_dict_merger

from .base import DataType

if TYPE_CHECKING:
    from oarepo_model.customizations.base import Customization
    from oarepo_model.utils import ArrayPathMember


class PolymorphicDataType(DataType):
    """Data type for handling polymorphic schemas with discriminator fields.

    This allows for fields that can be one of several different types based on a discriminator field.

    Supports schemas with a 'oneof' array where each item specifies a discriminator value
    and corresponding schema type. The discriminator field determines which schema variant
    to use for validation and serialization.

    Example:
    This schema will support two types of items (person and organization):
       {
           "type": "polymorphic",
           "discriminator": "type",
           "oneof": [
               {"discriminator": "person", "type": "Person"},
               {"discriminator": "organization", "type": "Organization"}
           ]
       }

    Input will be:
    {
        field_name : {"type": "person", person_fields...}
    } or
    {
        field_name : {"type": "organization", organization_fields...}
    }

    """

    TYPE = "polymorphic"

    @override
    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> ma.fields.Field:
        """Create a Marshmallow field for polymorphic data type.

        Uses OneOf field with different schemas based on discriminator.
        """
        if element.get("marshmallow_field") is not None:
            mf = obj_or_import_string(element["marshmallow_field"])
            if mf is None or not isinstance(mf, ma.fields.Field):
                raise TypeError(
                    f"marshmallow_field must be an instance of marshmallow.fields.Field, got {mf}",
                )
            return mf

        # get discriminator field name
        discriminator = element.get("discriminator", "type")

        # create a custom polymorphic field that distinguishes what schema to use
        return PolymorphicField(
            discriminator=discriminator,
            alternatives=self._create_schema_fields(field_name, element),
            **self._get_marshmallow_field_args(field_name, element),
        )

    def _create_schema_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, ma.fields.Field]:
        """Create marshmallow fields for each schema variant."""
        schema_fields = {}
        oneof_schemas = element.get("oneof", [])

        for oneof_item in oneof_schemas:
            # get discriminator value (e.g. person) and schema for that value (e.g. Person)
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get class for this schema type
                datatype = self._registry.get_type(schema_type)

                # create a marshmallow field and save it
                schema_fields[discriminator_value] = datatype.create_marshmallow_field(
                    field_name=field_name,
                    element=_variant_element_without_discriminator(oneof_item),
                )

        return schema_fields

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, ma.fields.Field]:
        alternative_fields = {}
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])
        if not oneof_schemas:
            raise ValueError("Polymorphic type requires a non-empty 'oneof' list")

        # iterate through each variant
        for oneof_item in oneof_schemas:
            # get its disciminator and schema type
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get class for that specific datatype
                datatype = self._registry.get_type(schema_type)

                # get UI fields from that datatype, where attribute is disciminator value
                ui_fields = datatype.create_ui_marshmallow_fields(
                    field_name=field_name,
                    element=_variant_element_without_discriminator(oneof_item),
                )
                if not ui_fields:
                    # no UI transformation for this variant - the datatype base
                    # contract's normal answer (e.g. keyword, fulltext)
                    continue
                if len(ui_fields) > 1:
                    raise NotImplementedError(
                        "Current version can only handle 1 UI field in polymorphic type!",
                    )

                alternative_fields[discriminator_value] = next(iter(ui_fields.values()))

        # return custom marshmallow field that distinguishes what schema to use
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or PolymorphicField
        return {
            field_name: field_class(
                discriminator=discriminator,
                alternatives=alternative_fields,
            ),
        }

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the polymorphic data type.

        Emits the union of all variants' children (the UI-model counterpart of
        create_mapping's merged properties and JSON schema's oneOf branch merge),
        so a walk into a polymorphic node - e.g. an internal relation resolving
        its keys through one - finds the variant's fields instead of a leaf.

        Union conflict rules (in oneof declaration order, see
        _merge_polymorphic_variant_children):
        - structural/leaf keys (label, help, input, ...) come from the first
          variant declaring the child;
        - "required" is kept only when *every* declaring variant requires the
          child (a wrongly-required marker is worse than a missing one - the
          server validates the real per-variant rule anyway);
        - object children are merged recursively.

        Per-variant UI models are emitted under "variants", keyed by
        discriminator value, together with "discriminator", so a client that
        knows the selected variant (e.g. a deposit form) can use its exact
        labels/help. To keep the ui model small, each variant entry holds only
        the children that *differ* from the union (a lazily-resolved child can
        not be compared and is always kept) - clients look a child up in
        variants[value] first and fall back to the union, which is complete.
        """
        ret = super().create_ui_model(element, path)

        variants: dict[str, Any] = {}
        for oneof_item in element.get("oneof", []):
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")
            if not (discriminator_value and schema_type):
                continue
            datatype = self._registry.get_type(schema_type)
            variants[discriminator_value] = datatype.create_ui_model(
                _variant_element_without_discriminator(oneof_item),
                path,
            )

        children = _merge_polymorphic_variant_children(list(variants.values()))
        if children:
            ret["children"] = children
        if variants:
            ret["discriminator"] = element.get("discriminator", "type")
            ret["variants"] = _shrink_variants_to_diffs(variants, children)
        return ret

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create JSON schema for polymorphic type using oneOf."""
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])

        json_one_of_schemas = []

        # iterate through each variant
        for oneof_item in oneof_schemas:
            # get its disciminator and schema type
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get datatype class and generate json schema from it
                datatype = self._registry.get_type(schema_type)
                child_jsonschema = datatype.create_json_schema(_variant_element_without_discriminator(oneof_item))

                if "properties" not in child_jsonschema:
                    child_jsonschema = dict(child_jsonschema)  # make a copy to avoid modifying the original
                    child_jsonschema["properties"] = {}

                # only 1 value is allowed in this field (e.g. person or organization)
                child_jsonschema["properties"][discriminator] = {
                    "type": "string",
                    "const": discriminator_value,
                }

                # discriminator is a required field
                if "required" not in child_jsonschema:
                    child_jsonschema = dict(child_jsonschema)  # make a copy to avoid modifying the original
                    child_jsonschema["required"] = []
                if discriminator not in child_jsonschema["required"]:
                    child_jsonschema["required"].append(discriminator)

                json_one_of_schemas.append(child_jsonschema)

        return {
            "oneOf": json_one_of_schemas,
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        Uses object type with properties from all possible schemas.
        """
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])

        all_properties = {discriminator: {"type": "keyword"}}

        # iterate through each variant
        for oneof_item in oneof_schemas:
            # get its discriminator and schema type
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get datatype class and generate mapping from it
                datatype = self._registry.get_type(schema_type)
                child_mapping = datatype.create_mapping(_variant_element_without_discriminator(oneof_item))

                # dump all properties from all variants in 1 dictionary
                if "properties" in child_mapping:
                    all_properties = readonly_dict_merger.merge(
                        all_properties,
                        child_mapping["properties"],
                    )

        return {"type": "object", "properties": all_properties}

    @override
    def visit(self, element: dict[str, Any], path: list[str], visitor: Any) -> None:
        """Visit polymorphic data type and all variants."""
        super().visit(element, path, visitor)
        for oneof_item in element.get("oneof", []):
            schema_type = oneof_item.get("type")
            if schema_type:
                self._registry.get_type(schema_type).visit(
                    _variant_element_without_discriminator(oneof_item), path, visitor
                )

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
    ) -> list[Customization]:
        """Create relations declared by the variants, same as visit descends into them.

        Without this, a relation (pid/internal/lazy) declared as a property of a
        polymorphic variant would be built everywhere (schema, mapping, UI model)
        but never registered as a relation system field.

        Variants typically repeat the same relation on purpose (every variant
        carrying, say, an `organism` vocabulary field); identical duplicates
        (same name *and* definition) collapse to one registration. Duplicates
        that differ (same field name, different vocabulary/keys/...) raise -
        a silent last-one-wins must not hide the conflict.
        """
        relations: list[Customization] = []
        for oneof_item in element.get("oneof", []):
            schema_type = oneof_item.get("type")
            if schema_type:
                relations.extend(
                    self._registry.get_type(schema_type).create_relations(
                        _variant_element_without_discriminator(oneof_item),
                        path,
                    )
                )
        return _dedupe_variant_relations(relations)


class PolymorphicField(ma.fields.Field):
    """Custom marshmallow field class that supports handling polymorphic fields."""

    default_error_messages: Mapping[str, str] = {"unknown_type": "Unknown type '{type}'."}

    def __init__(
        self,
        discriminator: str,
        alternatives: dict[str, ma.fields.Field],
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize a PolymorphicField for handling discriminated union types.

        :param discriminator:
            The field name used to determine which schema variant to use.
            Defaults to "type".
        :param alternatives:
            A mapping from discriminator values (e.g. person/organization)
            to marshmallow field instances. Each field handles validation and
            serialization for its corresponding object variant. Defaults to empty dict.
        """
        super().__init__(*args, **kwargs)
        self.discriminator = discriminator
        self.alternatives = alternatives

    def get_discriminator_value(self, obj: Any) -> str:
        """Get the discriminator value from the object."""
        val = get_value(
            obj,
            self.discriminator,
        )

        if val is missing_:
            error = self.make_error(key="required")
            error.field_name = self.discriminator
            raise error

        if not isinstance(val, str):
            error = ma.ValidationError("Discriminator value must be a string.")
            error.field_name = self.discriminator
            raise error

        return val

    def merged_schema(self) -> ma.Schema:
        """Return a schema with the fields of all variants, for walking a path through this field.

        The variant is only known per value (via the discriminator), so a path that goes
        through a polymorphic field sees the union of all variants' fields - the same way
        as its JSON schema/mapping. On a field name clash, the first variant wins.
        """
        merged: dict[str, ma.fields.Field] = {}
        for alternative in self.alternatives.values():
            if isinstance(alternative, ma.fields.Nested):
                for name, field in alternative.schema.fields.items():
                    # no copy needed: Schema.__init__ deep-copies declared fields before binding them
                    # (marshmallow 3 and 4), so the variant's own fields stay bound to its schema
                    merged.setdefault(name, field)
        return ma.Schema.from_dict(merged, name="MergedPolymorphicSchema")()

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        """Serialize by choosing correct serializer depending on the discriminator value."""
        if not isinstance(value, dict):
            return value

        discriminator_value = self.get_discriminator_value(value)
        if discriminator_value in self.alternatives:
            schema_field = self.alternatives[discriminator_value]
            return schema_field._serialize(  # noqa SLF001 continuing with the schema field
                value,
                attr,
                obj,
                **kwargs,
            )

        return value

    @override
    def _deserialize(
        self,
        value: Any,
        attr: str | None,
        data: Any,
        **kwargs: Any,
    ) -> Any:
        """Deserialize by choosing correct deserializer depending on the discriminator value."""
        discriminator_value = self.get_discriminator_value(value)

        if discriminator_value not in self.alternatives:
            raise self.make_error("unknown_type", type=discriminator_value)

        schema_field = self.alternatives[discriminator_value]
        return schema_field._deserialize(  # noqa SLF001 continuing with the schema field
            value,
            attr,
            data,
            **kwargs,
        )


def _merge_polymorphic_variant_children(variant_ui_models: list[dict[str, Any]]) -> dict[str, Any]:
    """Union the "children" of per-variant UI models, in declaration order.

    Per child, the first declaring variant's node is the source of truth for
    label/help/input (variant-specific deviations end up under "variants" for
    a client that can pick); the merged "required" flag is kept only when every
    declaring variant requires the child, and object "children" are recursed
    into. Children declared by no variant do not exist, so a variant that drops
    a child does not remove it from the union.

    :param variant_ui_models: the full UI models of the variants, in oneof order.
    :return: the merged children mapping of the polymorphic node.
    """

    def _children_of(ui_model: Mapping[str, Any]) -> Mapping[str, Any]:
        # a variant ui model that is a lazily-resolved mapping (a variant that
        # is itself a lazy/internal relation) is opaque - resolving it here
        # would touch a model still being built; plain-dict children only
        if not isinstance(ui_model, dict):
            return {}
        return ui_model.get("children") or {}

    child_names: dict[str, None] = {}
    for ui_model in variant_ui_models:
        child_names.update(dict.fromkeys(_children_of(ui_model)))

    merged: dict[str, Any] = {}
    for name in child_names:
        declaring_nodes = [
            children[name] for ui_model in variant_ui_models if name in (children := _children_of(ui_model))
        ]
        merged[name] = _merge_child_node(declaring_nodes)
    return merged


def _merge_child_node(declaring_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge one child node across the variants declaring it - see _merge_polymorphic_variant_children.

    A child node that is a lazily-resolved mapping (ReferenceUIModel - an
    internal/lazy relation inside a variant) is kept as the first declaring
    variant's, untouched: inspecting its "children" would resolve it while the
    owning model is still being built, so there is nothing to union lazily.
    """
    plain_nodes = [node for node in declaring_nodes if isinstance(node, dict)]
    if len(plain_nodes) < len(declaring_nodes):
        # some declaring nodes are lazily-resolved mappings - keep the first
        # declaring variant's node untouched, whatever kind it is (deepcopy of
        # a lazy mapping is a fresh lazy mapping, never resolved)
        return copy.deepcopy(declaring_nodes[0])

    merged = copy.deepcopy(declaring_nodes[0])
    if not all(node.get("required") for node in declaring_nodes):
        merged.pop("required", None)
    if "children" in merged:
        child_ui_models = [node for node in declaring_nodes if isinstance(node.get("children"), dict)]
        if len(child_ui_models) > 1:
            merged["children"] = _merge_polymorphic_variant_children(child_ui_models)
    if "child" in merged:
        # an array node: merge the item nodes of the declaring variants with
        # the same rules, so a difference inside the items (e.g. one variant
        # marking an item field required) is not lost behind the first variant
        child_nodes = [node["child"] for node in declaring_nodes if isinstance(node.get("child"), dict)]
        if len(child_nodes) > 1:
            merged["child"] = _merge_child_node(child_nodes)
    return merged


def _relation_signature(customization: Customization) -> tuple[Any, ...]:
    """Build a comparable signature of a relation-field customization, for cross-variant dedup.

    Two variants often declare the same relation independently (say, the same
    vocabulary in every entity kind) - such duplicates build distinct but
    equivalent objects, so identity/eq comparisons do not work. The signature
    instead compares everything that defines the relation's behavior (name,
    customization class, path, copied keys, cache key, target path, extra
    kwargs and the pid field's identity parts), so identical duplicates
    collapse and differing ones are caught.
    """
    pid_field = getattr(customization, "pid_field", None)
    return (
        getattr(customization, "name", None),
        type(customization).__name__,
        _norm(getattr(customization, "path", None)),
        _norm(getattr(customization, "keys", None)),
        getattr(customization, "cache_key", None),
        getattr(customization, "target_path", None),
        _norm(getattr(customization, "kwargs", None)),
        _pid_field_identity(pid_field),
    )


def _pid_field_identity(pid_field: Any) -> tuple[Any, ...] | None:
    """Identity of a relation's pid field, without forcing lazy resolution.

    A LazyModelPIDFieldContext resolves its target model on *any* attribute
    access (__getattr__), which must not happen here (the model may still be
    building) - its own model_name is read directly instead. Everything else
    is identified by its class and any declared type context on the instance
    dict (a vocabulary's _type_id), never through property/attribute resolve.
    """
    if pid_field is None:
        return None
    instance_attrs = vars(pid_field) if hasattr(pid_field, "__dict__") else {}
    return (
        type(pid_field).__name__,
        instance_attrs.get("model_name"),
        instance_attrs.get("_type_id"),
    )


def _norm(value: Any) -> Any:
    """Hashable/comparable normal form of customization attributes."""
    if isinstance(value, list):
        return tuple(_norm(v) for v in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _norm(v)) for k, v in value.items()))
    return value


def _dedupe_variant_relations(relations: list[Customization]) -> list[Customization]:
    """Collapse identical per-variant relations; raise on conflicting duplicates."""
    seen: dict[tuple[Any, ...], Customization] = {}
    result: list[Customization] = []
    for customization in relations:
        name = getattr(customization, "name", None)
        signature = _relation_signature(customization)
        if name is None or name.startswith("__lazy_relations__"):
            # synthetic lazy groups are per-variant by design (random names)
            result.append(customization)
            continue
        if name in seen:
            previous = seen[name]
            if _relation_signature(previous) != signature:
                raise ValueError(
                    f"Conflicting relation definitions for {name!r} across polymorphic variants: "
                    f"{_relation_signature(previous)!r} vs {signature!r}"
                )
            continue  # identical duplicate - one registration is enough
        seen[name] = customization
        result.append(customization)
    return result


def _ui_equal(a: Any, b: Any) -> bool:
    """Deep equality of UI model nodes that never resolves a lazy mapping.

    Plain dict ``==`` descends into *nested* containers, and a lazy
    ReferenceUIModel a few levels down (e.g. an internal relation inside an
    array item inside a variant) resolves on iteration - which imports the
    model that is still being built and kills the build (review.md P3-F1).
    Identical lazy objects compare equal by identity; a different lazy (or a
    lazy vs a real value) counts as different, so the variant keeps it.
    """
    if a is b:
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_ui_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_ui_equal(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, Mapping) or isinstance(b, Mapping):
        # a lazily-resolved node on either side: can not compare without resolving -> kept
        return False
    return a == b


def _shrink_variants_to_diffs(
    variants: dict[str, dict[str, Any]],
    union_children: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Drop each variant's children that are identical to the union's.

    The union ("children" of the polymorphic node itself) is always complete,
    so a variant subtree identical to it carries no information - and the ui
    model is embedded into every deposit page. A child that is not a plain
    dict on either side (a lazily-resolved reference) can not be compared
    without resolving it (see _ui_equal), so it is always kept.
    """

    def _differs(name: str, node: Any) -> bool:
        union_node = union_children.get(name)
        return not (isinstance(node, dict) and isinstance(union_node, dict) and _ui_equal(node, union_node))

    shrunk: dict[str, dict[str, Any]] = {}
    for discriminator_value, variant in variants.items():
        variant_children = variant.get("children")
        if isinstance(variant_children, dict):
            # shallow copy: only the "children" mapping itself is replaced
            shrunk[discriminator_value] = {
                **variant,
                "children": {name: node for name, node in variant_children.items() if _differs(name, node)},
            }
        else:
            shrunk[discriminator_value] = variant
    return shrunk


def _variant_element_without_discriminator(oneof_item: dict[str, Any]) -> dict[str, Any]:
    """Return a oneof item without its "discriminator" (the variant's value, not a field name).

    A named variant type merges the element over its own definition - left in, the value would
    replace the discriminator field name of a nested polymorphic type.
    """
    return {key: value for key, value in oneof_item.items() if key != "discriminator"}
