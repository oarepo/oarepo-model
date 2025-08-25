#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring rdf service config links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.config import (
    RecordPIDLink,
    ThumbnailLinks,
    _groups_enabled,
    archive_download_enabled,
    has_doi,
    has_image_files,
    is_record,
    record_thumbnail_sizes,
    vars_preview_html,
    vars_self_iiif,
)
from invenio_records_resources.services import ConditionalLink, RecordEndpointLink
from invenio_records_resources.services.base.links import EndpointLink
from oarepo_runtime.services.config import has_draft
from werkzeug.local import LocalProxy

from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

record_doi_link = RecordPIDLink("https://doi.org/{+pid_doi}", when=has_doi)


class RDMServiceConfigLinks(Preset):
    """Preset for extra RDM service config links."""

    modifies = (
        "record_links_item",
        "record_search_item",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToDictionary(
            "record_links_item",
            {
                "preview_html": RecordEndpointLink(
                    "invenio_app_rdm_records.record_from_pid", vars=vars_preview_html, when=has_draft()
                ),
                # Parent
                # move parent links possibly to draft
                "parent": EndpointLink(
                    f"{model.blueprint_base}.read",
                    params=["pid_value"],
                    when=is_record,
                    vars=lambda record, variables: variables.update({"pid_value": record.parent.pid.pid_value}),
                ),
                # in tests handled by fake blueprint
                "parent_html": EndpointLink(
                    "invenio_app_rdm_records.record_detail",
                    params=["pid_value"],
                    when=is_record,
                    vars=lambda record, variables: variables.update({"pid_value": record.parent.pid.pid_value}),
                ),
                # TODO: uncomment to test DOI links as soon as oarepo-doi will be rdm13 compatible
                # "parent_doi": RecordPIDLink(
                #    "https://doi.org/{+parent_pid_doi}",
                #    when=is_record_or_draft_and_has_parent_doi,
                # ),
                # in tests handled by fake blueprint
                # "parent_doi_html": EndpointLink(
                #    "invenio_app_rdm_records.record_from_pid",
                #    params=["pid_value", "pid_scheme"],
                #    when=is_record_or_draft_and_has_parent_doi,
                #    vars=lambda record, vars: vars.update(
                #        {
                #            "pid_scheme": "doi",
                #            "pid_value": record.parent.pids["doi"]["identifier"],
                #        }
                #    ),
                # ),
                # "doi": record_doi_link,
                # "self_doi": record_doi_link,
                # in tests handled by fake blueprint
                # "self_doi_html": EndpointLink(
                #    "invenio_app_rdm_records.record_from_pid",
                #    params=["pid_value", "pid_scheme"],
                #    when=is_record_and_has_doi,
                #    vars=lambda record, vars: vars.update(
                #        {
                #            "pid_scheme": "doi",
                #            "pid_value": record.pids["doi"]["identifier"],
                #        }
                #    ),
                # ),
                # in tests handled by fake blueprint
                "self_iiif_manifest": EndpointLink("iiif.manifest", params=["uuid"], vars=vars_self_iiif),
                "self_iiif_sequence": EndpointLink("iiif.sequence", params=["uuid"], vars=vars_self_iiif),
                # Files
                "files": ConditionalLink(
                    cond=is_record,
                    if_=RecordEndpointLink(f"{model.blueprint_base}_files.search"),
                    else_=RecordEndpointLink(f"{model.blueprint_base}_files.search"),
                ),
                "media_files": ConditionalLink(
                    cond=is_record,
                    if_=RecordEndpointLink(f"{model.blueprint_base}_media_files.search"),
                    else_=RecordEndpointLink(f"{model.blueprint_base}_media_files.search"),
                ),
                "thumbnails": ThumbnailLinks(
                    sizes=LocalProxy(record_thumbnail_sizes),
                    when=has_image_files,
                ),
                # Reads a zipped version of all files
                "archive": ConditionalLink(
                    cond=is_record,
                    if_=RecordEndpointLink(
                        f"{model.blueprint_base}_files.read_archive",
                        when=archive_download_enabled,
                    ),
                    else_=RecordEndpointLink(
                        f"{model.blueprint_base}_files.read_archive",
                        when=archive_download_enabled,
                    ),
                ),
                "archive_media": ConditionalLink(
                    cond=is_record,
                    if_=RecordEndpointLink(
                        f"{model.blueprint_base}_media_files.read_archive",
                        when=archive_download_enabled,
                    ),
                    else_=RecordEndpointLink(
                        f"{model.blueprint_base}_media_files.read_archive",
                        when=archive_download_enabled,
                    ),
                ),
                # Access
                # in tests handled access links by fake blueprint
                # Need to wait for oarepo-rdm, those blueprints are not defined now
                "access_links": RecordEndpointLink(f"{model.blueprint_base}_links.search"),
                "access_grants": RecordEndpointLink(f"{model.blueprint_base}_grants.search"),
                "access_users": RecordEndpointLink(f"{model.blueprint_base}_user_access.search"),
                "access_groups": RecordEndpointLink(
                    f"{model.blueprint_base}_group_access.search",
                    when=_groups_enabled,
                ),
                # Working out of the box
                "access_request": RecordEndpointLink(f"{model.blueprint_base}.create_access_request"),
                "access": RecordEndpointLink(f"{model.blueprint_base}.update_access_settings"),
            },
        )
