def test_custom_fields(
    app,
    identity_simple,
    records_cf_model,
    input_data,
    search,
    search_clear,
    location,
):
    service = records_cf_model.proxies.current_service

    # Create an item
    item = service.create(
        identity_simple,
        {**input_data, "custom_fields": {"cern:experiment": "CMS"}},
    )
    id_ = item.id

    # Read it
    read_item = service.read(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data
    assert read_item.data["custom_fields"]["cern:experiment"] == "CMS"


def test_draft_custom_fields(
    drafts_cf_model,
    app,
    identity_simple,
    input_data_with_files_disabled,
    search,
    search_clear,
    location,
):
    service = drafts_cf_model.proxies.current_service
    schema = drafts_cf_model.RecordSchema

    # Create an item
    item = service.create(
        identity_simple,
        {**input_data_with_files_disabled, "custom_fields": {"cern:experiment": "CMS"}},
    )
    id_ = item.id

    # Read it
    read_item = service.read_draft(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data
    assert read_item.data["custom_fields"]["cern:experiment"] == "CMS"

    published_item = service.publish(identity_simple, id_)
    assert published_item.id == id_
    assert published_item.data["custom_fields"]["cern:experiment"] == "CMS"
