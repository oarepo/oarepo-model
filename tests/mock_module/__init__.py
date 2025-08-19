#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Mock module for blueprints."""

from __future__ import annotations

from flask import Blueprint


def create_invenio_app_rdm_records_blueprint(app):
    """Create fake invenio_app_rdm_records Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "invenio_app_rdm_records",
        __name__,
    )

    def record_file_download(pid_value, file_item=None, is_preview=False, **kwargs: object) -> object:
        """Fake record_file_download view function."""
        return "<file content>"

    def record_detail(pid_value, file_item=None, is_preview=False, **kwargs: object) -> object:
        """Fake record_detail view function."""
        return "<record detail>"

    def deposit_edit(pid_value, file_item=None, is_preview=False, **kwargs: object) -> object:
        """Fake record_detail view function."""
        return "<deposit edit>"

    def record_latest(record=None, **kwargs: object) -> object:
        """Fake record_latest view function."""
        return "<record latest>"

    def record_from_pid(record=None, **kwargs: object) -> object:
        """Fake record_from_pid view function."""
        return "<record from pid>"

    # Records URL rules
    blueprint.add_url_rule(
        "/records/<pid_value>/files/<path:filename>",
        view_func=record_file_download,
    )

    blueprint.add_url_rule(
        "/records/<pid_value>",
        view_func=record_detail,
    )

    blueprint.add_url_rule(
        "/uploads/<pid_value>",
        view_func=deposit_edit,
    )

    blueprint.add_url_rule(
        "/records/<pid_value>/latest",
        view_func=record_latest,
    )

    blueprint.add_url_rule(
        "/pid_scheme/<path:pid_value>",
        view_func=record_from_pid,
    )

    return blueprint


def create_invenio_app_rdm_iiif_blueprint(app):
    """Create fake invenio_app_rdm_iiif Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint("iiif", __name__, url_prefix="/iiif")

    def manifest(*args: object, **kwargs: object) -> object:
        """Fake IIIF manifest view function."""
        return "<IIIF manifest>"

    def sequence(*args: object, **kwargs: object) -> object:
        """Fake IIIF sequence view function."""
        return "<IIIF sequence>"

    def image_api(*args: object, **kwargs: object) -> object:
        """Fake IIIF image API view function."""
        raise ValueError("Image API not implemented")
        return "<IIIF image API>"

    # Records URL rules
    blueprint.add_url_rule(
        "/<path:uuid>/manifest",
        view_func=manifest,
    )

    blueprint.add_url_rule(
        "/<path:uuid>/sequence/default",
        view_func=sequence,
    )

    blueprint.add_url_rule(
        "/<path:uuid>/<region>/<size>/<rotation>/<quality>.<image_format>",
        view_func=image_api,
    )

    return blueprint


def create_invenio_app_rdm_access_links_blueprint(app):
    """Create fake invenio_app_rdm_access_links Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "rdm_test_links",
        __name__,
    )

    def search(*args: object, **kwargs: object) -> object:
        """Fake search view function."""
        return "<search>"

    # Records URL rules
    blueprint.add_url_rule(
        "/rdm-test/<pid_value>/access/links",
        view_func=search,
    )

    return blueprint


def create_invenio_app_rdm_access_grants_blueprint(app):
    """Create fake invenio_app_rdm_access_grants Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "rdm_test_grants",
        __name__,
    )

    def search(*args: object, **kwargs: object) -> object:
        """Fake search view function."""
        return "<search>"

    # Records URL rules
    blueprint.add_url_rule(
        "/rdm-test/<pid_value>/access/grants",
        view_func=search,
    )

    return blueprint


def create_invenio_app_rdm_user_access_blueprint(app):
    """Create fake invenio_app_rdm_user_access Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "rdm_test_user_access",
        __name__,
    )

    def search(*args: object, **kwargs: object) -> object:
        """Fake search view function."""
        return "<search>"

    # Records URL rules
    blueprint.add_url_rule(
        "/rdm-test/<pid_value>/access/users",
        view_func=search,
    )

    return blueprint


def create_invenio_app_rdm_group_access_blueprint(app):
    """Create fake invenio_app_rdm_group_access Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "rdm_test_group_access",
        __name__,
    )

    def search(*args: object, **kwargs: object) -> object:
        """Fake search view function."""
        return "<search>"

    # Records URL rules
    blueprint.add_url_rule(
        "/rdm-test/<pid_value>/access/groups",
        view_func=search,
    )

    return blueprint
