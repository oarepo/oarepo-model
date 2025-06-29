import pytest
from invenio_pidstore.errors import PIDDeletedError


def test_simple_flow(
    app, test_service, identity_simple, input_data, empty_model, search_clear
):
    Record = empty_model.Record

    # Create an item
    item = test_service.create(identity_simple, input_data)
    id_ = item.id

    # Read it
    read_item = test_service.read(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # Refresh to make changes live
    Record.index.refresh()

    # Search it
    res = test_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 1
    assert list(res.hits)[0] == read_item.data

    # Scan it
    res = test_service.scan(identity_simple, q=f"id:{id_}")
    assert res.total is None
    assert list(res.hits)[0] == read_item.data

    # Update it
    data = read_item.data
    data["metadata"]["title"] = "New title"
    update_item = test_service.update(identity_simple, id_, data)
    assert item.id == update_item.id
    assert update_item["metadata"]["title"] == "New title"

    # Delete it
    assert test_service.delete(identity_simple, id_)

    # Refresh to make changes live
    Record.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, test_service.read, identity_simple, id_)
    # - search
    res = test_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0
