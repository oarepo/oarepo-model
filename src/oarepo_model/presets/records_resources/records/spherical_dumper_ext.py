#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Spherical coordinate dumper extensions generated from model data types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from shapely import wkt as shapely_wkt
from shapely.geometry import mapping as shapely_mapping
from shapely.geometry import shape as shapely_shape

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.datatypes.base import ARRAY_ITEM_PATH
from oarepo_model.datatypes.spherical import (
    ICRSDataType,
    ICRSShapeDataType,
    icrs_shape_to_lon_lat,
    lat_lon_to_ra_dec,
    lon_lat_to_icrs_shape,
    ra_dec_to_lat_lon,
)
from oarepo_model.datatypes.tree import get_model_nodes
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.records.path_dumper_ext import PathDumperExtBase

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from shapely.geometry.base import BaseGeometry

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


def _apply_to_values(value: Any, convert: Callable[[Any], Any]) -> Any:
    """Apply ``convert`` to a value, or to every item of a list of such values."""
    if value is None:
        return None
    if isinstance(value, list):
        return [_apply_to_values(item, convert) for item in value]
    return convert(value)


def _point_to_opensearch(value: dict[str, Any]) -> dict[str, Any]:
    """Convert one ICRS point to the lat/lon a geo_point field expects."""
    lat, lon = ra_dec_to_lat_lon(value["ra"], value["dec"])
    return {"lat": lat, "lon": lon}


def _point_from_opensearch(value: dict[str, Any]) -> dict[str, Any]:
    """Convert one geo_point value back to an ICRS point."""
    ra, dec = lat_lon_to_ra_dec(value["lat"], value["lon"])
    return {"ra": ra, "dec": dec}


class ICRSDumperExt(PathDumperExtBase):
    """Dump ICRS into geo_point fields."""

    def _data_to_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert a icrs field to geo_point field."""
        data[key] = _apply_to_values(data[key], _point_to_opensearch)

    def _data_from_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert a geo_point field to a icrs field."""
        data[key] = _apply_to_values(data[key], _point_from_opensearch)


def _to_geometry(value: Any) -> BaseGeometry:
    """Read a shape value, either a WKT string or a GeoJSON object, with shapely."""
    return shapely_wkt.loads(value) if isinstance(value, str) else shapely_shape(value)


def _shape_to_opensearch(value: Any) -> dict[str, Any]:
    """Convert one ICRS shape to the GeoJSON lon/lat a geo_shape field expects.

    A WKT shape necessarily becomes GeoJSON, which is the format OpenSearch's
    geo_shape query and aggregations work with anyway.
    """
    return shapely_mapping(icrs_shape_to_lon_lat(_to_geometry(value)))


def _shape_from_opensearch(value: Any) -> dict[str, Any]:
    """Convert one indexed GeoJSON shape back to ICRS coordinates.

    Always yields GeoJSON: a shape that was given as WKT is indexed as GeoJSON,
    so its textual form is not round-tripped.
    """
    return shapely_mapping(lon_lat_to_icrs_shape(_to_geometry(value)))


class ICRSShapeDumperExt(PathDumperExtBase):
    """Dump ICRS shapes into geo_shape fields."""

    def _data_to_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert a icrs_shape field to a geo_shape field."""
        data[key] = _apply_to_values(data[key], _shape_to_opensearch)

    def _data_from_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert a geo_shape field to a icrs_shape field."""
        data[key] = _apply_to_values(data[key], _shape_from_opensearch)


def _strip_array_item(path: list[str]) -> list[str]:
    """Drop a trailing array marker from a model path.

    ``PathDumperExtBase`` can only convert a value reachable by a dict key, so a
    path ending with ``[]`` (an array whose items are ICRS values) would never
    reach a converter; the converters handle lists of values themselves instead.
    """
    return path[:-1] if path and path[-1] == ARRAY_ITEM_PATH else path


class ICRSDumperExtPreset(Preset):
    """Preset that converts icrs fields to geo_point opensearch fields and vice versa."""

    modifies = ("record_dumper_extensions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        paths = [
            _strip_array_item(path)
            for _datatype, path in get_model_nodes(
                builder,
                model,
                lambda datatype: isinstance(datatype, ICRSDataType),
                unique=True,
            )
        ]

        if paths:
            yield AddToList("record_dumper_extensions", ICRSDumperExt(paths))


class ICRSShapeDumperExtPreset(Preset):
    """Preset that converts icrs_shape fields to geo_shape opensearch fields and vice versa."""

    modifies = ("record_dumper_extensions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        paths = [
            _strip_array_item(path)
            for _datatype, path in get_model_nodes(
                builder,
                model,
                lambda datatype: isinstance(datatype, ICRSShapeDataType),
                unique=True,
            )
        ]

        if paths:
            yield AddToList("record_dumper_extensions", ICRSShapeDumperExt(paths))
