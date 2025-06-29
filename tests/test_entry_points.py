from importlib.metadata import entry_points

from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_resources_presets


def test_create_default_model():
    my_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets],
    )
    my_model.register()

    check_entry_point(
        "invenio_base.api_apps",
        "test",
        "runtime_models_test:ext",
    )
    check_entry_point("invenio_base.apps", "test", "runtime_models_test:ext")
    check_entry_point("invenio_db.models", "test", "runtime_models_test")
    check_entry_point("invenio_search.mappings", "test", "runtime_models_test.mappings")
    check_entry_point(
        "invenio_jsonschemas.schemas",
        "test",
        "runtime_models_test.jsonschemas",
    )
    check_entry_point(
        "invenio_base.blueprints",
        "test",
        "runtime_models_test.blueprints:create_app_blueprint",
    )
    check_entry_point(
        "invenio_base.api_blueprints",
        "test",
        "runtime_models_test.blueprints:create_api_blueprint",
    )


def check_entry_point(group: str, name: str, value: str):
    ep = entry_points(group=group, name=name)
    assert len(ep) == 1, (
        f"Entry point {group}:{name} not found. Found entry points: {[x.name for x in entry_points(group=group)]}"
    )

    ep_value = next(iter(ep)).value

    assert ep_value == value, (
        f"Entry point {group}:{name} has wrong value: {ep_value} != {value}"
    )

    try:
        next(iter(ep)).load()
    except Exception as e:
        raise AssertionError(
            f"Entry point {group}:{name}:{ep_value} could not be loaded: {e}"
        ) from e
