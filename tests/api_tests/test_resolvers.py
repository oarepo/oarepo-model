#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from flask_principal import Need
from oarepo_runtime.typing import record_from_result


def _resolver_test(service, tested_record, tested_item, resolver) -> None:
    assert resolver.matches_entity(tested_record)

    reference = resolver.reference_entity(tested_record)
    assert reference == {service.id: tested_item.id}
    assert resolver.matches_reference_dict(reference)


def _proxy_test(proxy, tested_record, tested_item, identity) -> None:
    assert proxy.resolve() == tested_record

    resolved_fields = proxy.pick_resolved_fields(identity, tested_item.to_dict())
    assert resolved_fields["links"] == tested_item.links
    assert resolved_fields["id"] == tested_item.id
    assert len(resolved_fields) == 2

    needs = proxy.get_needs(ctx={"record_permission": "read"})
    assert needs == {Need(method="system_role", value="any_user"), Need(method="system_role", value="system_process")}


def test_draft(
    app,
    test_draft_service,
    identity_simple,
    input_data_with_files_disabled,
    draft_model,
    search,
    search_clear,
    location,
):
    tested_item = test_draft_service.create(identity_simple, input_data_with_files_disabled)
    tested_record = record_from_result(tested_item)
    service = test_draft_service
    model = draft_model
    resolver = model.RecordResolver(
        model.Record, service_id=service.id, type_key=service.id, proxy_cls=model.RecordProxy
    )

    _resolver_test(service, tested_record, tested_item, resolver)
    assert resolver.matches_entity(tested_record)

    reference = resolver.reference_entity(tested_record)
    assert reference == {service.id: tested_item.id}

    proxy = resolver.get_entity_proxy(reference)
    _proxy_test(proxy, tested_record, tested_item, identity_simple)

    resolved_fields = proxy.pick_resolved_fields(identity_simple, tested_item.to_dict())
    ghost_record = proxy.ghost_record({"id": tested_item.id})
    assert ghost_record == resolved_fields


def test_published_record(
    app,
    draft_service_with_files,
    draft_file_service,
    identity_simple,
    input_data,
    draft_model_with_files,
    add_file_to_draft,
    search,
    search_clear,
    location,
):
    Draft = draft_model_with_files.Draft
    service = draft_service_with_files
    model = draft_model_with_files

    # Create an item
    item = service.create(identity_simple, input_data)
    id_ = item.id
    Draft.index.refresh()

    # Add a file
    add_file_to_draft(draft_file_service, id_, "test.txt", identity_simple)

    tested_item = service.publish(identity_simple, id_)

    tested_record = record_from_result(tested_item)
    resolver = model.RecordResolver(
        model.Record, service_id=service.id, type_key=service.id, proxy_cls=model.RecordProxy
    )

    _resolver_test(service, tested_record, tested_item, resolver)
    assert resolver.matches_entity(tested_record)

    reference = resolver.reference_entity(tested_record)
    assert reference == {service.id: tested_item.id}

    proxy = resolver.get_entity_proxy(reference)
    _proxy_test(proxy, tested_record, tested_item, identity_simple)

    ghost_record = proxy.ghost_record({"id": tested_item.id})
    assert ghost_record == {"id": {"id": tested_item.id}}  # produced by invenio


def test_model_without_drafts(
    app,
    test_service,
    file_service,
    identity_simple,
    input_data,
    empty_model,
    search,
    search_clear,
    location,
):
    # Create an item
    model = empty_model
    service = test_service

    tested_item = test_service.create(identity_simple, input_data)
    tested_record = record_from_result(tested_item)
    resolver = model.RecordResolver(
        model.Record, service_id=service.id, type_key=service.id, proxy_cls=model.RecordProxy
    )

    _resolver_test(service, tested_record, tested_item, resolver)
    assert resolver.matches_entity(tested_record)

    reference = resolver.reference_entity(tested_record)
    assert reference == {service.id: tested_item.id}

    proxy = resolver.get_entity_proxy(reference)
    _proxy_test(proxy, tested_record, tested_item, identity_simple)

    # TODO: base RecordProxy has no ghost_record


def test_not_matching(
    app,
    identity_simple,
    input_data_with_files_disabled,
    draft_model,
    draft_model_with_files,
    test_draft_service,
    draft_service_with_files,
    test_service,
    search,
    search_clear,
    location,
):
    tested_item = test_draft_service.create(identity_simple, input_data_with_files_disabled)
    tested_record = record_from_result(tested_item)
    correct_resolver = draft_model.RecordResolver(
        draft_model.Record,
        service_id=test_draft_service.id,
        type_key=test_draft_service.id,
        proxy_cls=draft_model.RecordProxy,
    )

    with_files_resolver = draft_model_with_files.RecordResolver(
        draft_model_with_files.Record,
        service_id=draft_service_with_files.id,
        type_key=draft_service_with_files.id,
        proxy_cls=draft_model_with_files.RecordProxy,
    )
    assert not with_files_resolver.matches_entity(tested_record)

    correct_reference = correct_resolver.reference_entity(tested_record)
    assert not with_files_resolver.matches_reference_dict(correct_reference)
