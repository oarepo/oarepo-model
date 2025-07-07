import pytest
from invenio_pidstore.errors import PIDDoesNotExistError


def test_simple_flow(
    app,
    test_draft_service,
    identity_simple,
    input_data_with_files_disabled,
    draft_model,
    search,
    search_clear,
    location,
):
    Record = draft_model.Record
    Draft = draft_model.DraftRecord

    # Create an item
    item = test_draft_service.create(identity_simple, input_data_with_files_disabled)
    id_ = item.id

    # Read it
    read_item = test_draft_service.read_draft(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # Refresh to make changes live
    Draft.index.refresh()

    # Search it
    res = test_draft_service.search_drafts(
        identity_simple, q=f"id:{id_}", size=25, page=1
    )
    assert res.total == 1
    first_hit = list(res.hits)[0]
    assert first_hit["metadata"] == read_item.data["metadata"]
    assert first_hit["links"].items() <= read_item.links.items()

    # Update it
    data = read_item.data
    data["metadata"]["title"] = "New title"
    update_item = test_draft_service.update_draft(identity_simple, id_, data)
    assert item.id == update_item.id
    assert update_item["metadata"]["title"] == "New title"

    print("Updated item:", update_item.data)

    # Can not publish as publishing needs files support in drafts
    # assert test_draft_service.publish(identity_simple, id_)

    test_draft_service.delete_draft(identity_simple, id_)
    Draft.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDoesNotExistError, test_draft_service.read, identity_simple, id_)
    # - search
    res = test_draft_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0
