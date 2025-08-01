def test_vocabularies(
    app,
    identity_simple,
    empty_model,
    vocabulary_model,
    vocabulary_fixtures,
    search,
    search_clear,
    location,
):

    Record = vocabulary_model.Record
    record_with_vocabulary_service = vocabulary_model.proxies.current_service

    vocabulary_rec = record_with_vocabulary_service.create(
        identity_simple,
        {
            "files": {
                "enabled": False,
            },
            "metadata": {
                "language": {
                    "id": "en",
                },
                "affiliation": {"id": "02ex6cf31"},
                "funder": {
                    "id": "05k73zm37",
                },
                "award": {
                    "id": "01cwqze88::1R01HL141112-01",
                },
                "subject": {"id": "ab"},
            },
        },
    )

    md = vocabulary_rec.data["metadata"]

    import json

    print(json.dumps(md, indent=2))

    assert md == {
        "language": {"id": "en", "title": {"cs": "Angličtina", "en": "English"}},
        "affiliation": {
            "id": "02ex6cf31",
            "name": "Brookhaven National Laboratory",
            "identifiers": [{"scheme": "ror", "identifier": "02ex6cf31"}],
        },
        "funder": {
            "id": "05k73zm37",
            "name": "Academy of Finland",
        },
        "award": {
            "id": "01cwqze88::1R01HL141112-01",
            "title": {
                "en": "Studies of mRNA translational regulations in erythropoiesis"
            },
            "number": "1R01HL141112-01",
            "identifiers": [
                {"scheme": "doi", "identifier": "10.1234/01cwqze88::1R01HL141112-01"}
            ],
            "acronym": "mRNA",
            "program": "NATIONAL_HEART,_LUNG,_AND_BLOOD_INSTITUTE",
        },
        "subject": {
            "id": "ab",
            "subject": "Agricultural biotechnology",
            "scheme": "FOS",
            "props": {
                "classification": "FOS",
            },
        },
    }
