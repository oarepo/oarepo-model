def test_relations(
    app,
    identity_simple,
    empty_model,
    relation_model,
    search,
    search_clear,
    location,
):

    TargetRecord = empty_model.Record
    target_service = empty_model.proxies.current_service

    # Create the target records

    rec1_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 1"}},
    ).id
    rec2_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 2"}},
    ).id
    rec3_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 3"}},
    ).id

    # Refresh to make changes live
    TargetRecord.index.refresh()

    RelationRecord = relation_model.Record
    relation_service = relation_model.proxies.current_service
    RelationSchema = relation_model.RecordSchema

    relation_rec = relation_service.create(
        identity_simple,
        {
            "files": {
                "enabled": False,
            },
            "metadata": {
                "direct": {
                    "id": rec1_id,
                },
                "array": [
                    {"id": rec1_id},
                    {"id": rec2_id},
                ],
                "object": {
                    "a": {"id": rec1_id},
                },
                "double_array": [
                    {"array": [{"id": rec1_id}, {"id": rec2_id}]},
                    {"array": [{"id": rec3_id}]},
                ],
            },
        },
    )

    md = relation_rec.data["metadata"]
    assert md["direct"]["id"] == rec1_id
    assert md["direct"]["metadata"]["title"] == "Record 1"

    assert len(md["array"]) == 2
    assert md["array"][0]["id"] == rec1_id
    assert md["array"][0]["metadata"]["title"] == "Record 1"
    assert md["array"][1]["id"] == rec2_id
    assert md["array"][1]["metadata"]["title"] == "Record 2"

    assert md["object"]["a"]["id"] == rec1_id
    assert md["object"]["a"]["metadata"]["title"] == "Record 1"

    assert len(md["double_array"]) == 2
    assert len(md["double_array"][0]["array"]) == 2
    assert md["double_array"][0]["array"][0]["id"] == rec1_id
    assert md["double_array"][0]["array"][0]["metadata"]["title"] == "Record 1"
    assert md["double_array"][0]["array"][1]["id"] == rec2_id
    assert md["double_array"][0]["array"][1]["metadata"]["title"] == "Record 2"
    assert len(md["double_array"][1]["array"]) == 1
    assert md["double_array"][1]["array"][0]["id"] == rec3_id
    assert md["double_array"][1]["array"][0]["metadata"]["title"] == "Record 3"
