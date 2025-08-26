# OARepo model customizations and builders

This package provides a way of building an Invenio model with user customizations.
It allows you to add mixins, classes to components, routes, and other customizations
to the model while ensuring that the model remains consistent, functional and upgradable.

## High-level API

At first, create a model using the `model` function from `oarepo_model.api` and
include the necessary presets.

```python
# mymodel.py

from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_resources_presets
from oarepo_model.presets.drafts import drafts_presets


my_model = model(
    "my_model",
    version="1.0.0",
    presets=[
    records_resources_presets,
    drafts_presets,
    ],
    customizations=[
    ],
)
```

Then you need to register the model before Invenio is initialized. The best way is
to do it in the `invenio.cfg` file:

```python
# invenio.cfg

from mymodel import my_model

my_model.register()
```

## Adding customizations

You can add customizations to the model by using the `customizations` parameter
of the `model` function. The following customizations are available, importable from
`oarepo_model.customizations`:

| Name | Description |
| ---- | ----------- |
| **classes** |      |
| `AddClass(name)` | Adds a new class to the model. |
| `AddBaseClasses(name, *base_classes)` | Adds a base class to a model class. |
| `AddMixins(name, *mixins)` | Adds mixins to the model. |
| `ChangeBase(name, old_base, new_base)` | Changes the base class of the model. |
| **modules** |      |
| `AddModule(name, exists_ok=False)` | Adds a module to the model. |
| `AddToModule(module_name, property_name, value, exists_ok=False)` | Adds a property to a module in the model. |
| `AddFileToModule` | Adds a file to the module. |
| **lists** |      |
| `AddList(name, exists_ok=False)` | Adds a new list to the model. |
| `AddClassList(name, exists_ok=False)` | Adds a new class list to the model. A class list keeps an MRO-consistent order of classes and can be used later as bases for a generated class. If this ordering functionality is not required, use `AddList`. |
| `AddToList(list_name, value, exists_ok=False)` | Appends a value to an existing list in the model. Set `exists_ok=True` to allow duplicates. |
| **dicts** |      |
| `AddDictionary(name, default=None, exists_ok=False)` | Adds a dictionary to the model. |
| `AddToDictionary(name, {..}...)` or `AddToDictionary(name, key=..., value=..., patch=False)` | Adds entries to a dictionary in the model (optionally merge with `patch=True`). |
| **entry points** |      |
| `AddEntryPoint` | Adds an entry point to the model. |
| **high-level** |       |
| `AddMetadataExport(**export)` | Adds a serializer for metadata exports. |
| `AddPIDRelation(name, path, keys, pid_field, ...)` | Declares a PID relation system field based on a path (supports list and nested-list relations). |
| `SetPermissionPolicy(policy_class)` | Sets the permission policy for the model. |

### Extending class with a mixin

To add a mixin to a class in the model, you can use the `AddMixins` customization.
Mixins are prepended to the class, so they take precedence in the MRO. If the resulting
MRO would be inconsistent, it is automatically reordered to a consistent order.

```python
from oarepo_model.customizations import AddMixins
from my_mixins import BaseMixin

my_model = model(
    "my_model",
    version="1.0.0",
    presets=[
    records_resources_presets,
    drafts_presets,
    ],
    customizations=[
    AddMixins("Record", BaseMixin),
    ],
)
```

### Adding a new service component

```python
from oarepo_model.customizations import AddToList

class MyComponent:
    ...

my_model = model(
    "my_model",
    version="1.0.0",
    presets=[
        records_resources_presets,
        drafts_presets,
    ],
    customizations=[
        AddToList("record_service_components", MyComponent),
    ],
)
```

### Generating metadata schema via data types

To generate `RecordSchema`/`MetadataSchema` from a type definition, pass `types` and set `metadata_type` to the name of the root type:

```python
from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_resources_presets

my_model = model(
    "my_model",
    version="1.0.0",
    presets=[records_resources_presets],
    types=[
        {
            "RecordMetadata": {
                "properties": {
                    "title": {"type": "fulltext+keyword", "required": True},
                },
            }
        }
    ],
    metadata_type="RecordMetadata",
)
```



## Behind the scenes

When the model is created, the following steps are performed:

1. An instance of `InvenioModel` is created. This instance holds the basic configuration
   of the model, such as its name, version, api and ui slugs.

2. An instance of  an `InvenioModelBuilder` is created.

3. All presets are collected and sorted according to their dependencies.

4. For each preset
   1. Dependencies of the preset are collected, including those that were passed
      as `customizations` to the model. If the dependency has not yet been build,
      it is at this moment.
   2. the `apply` method is called with the builder and the model. The method returns
      a list of customizations that are applied to the model.

5. If there are an unapplied customizations, they are applied to the model.

6. During the applications of the customizations, instances of `Partial` are created
   within the builder, such as `BuilderClass`, `BuilderList`, `BuilderModule`. These
   instances provide a recipe for a part of the final model. The part is built either
   if it is needed by a preset/customization or at the end of the model building process.

7. The result of the model building process is transformed into a SimpleNamespace
   and returned to the caller.
    The returned object also provides helpers:
    - `register()` / `unregister()` — to register the in-memory model for import/entry points
    - `get_resources()` — to retrieve the in-memory files as a `{path: content}` mapping

## Registering the model

Invenio needs some parts of the model to be registered via entry points. We provide
a `register` method on the model instance that automatically adds the model to the
entry points via registering a new importer to `sys.meta_path`. This allows
Invenio to find model components in the entry points and use them during the
initialization process.

The call needs to be done before Invenio is initialized, so that's why the best place
to do it is in the `invenio.cfg` file.

## Design decisions

### Late binding


The classes within the model should be as loosely coupled as possible. This is implemented
by using dependency injection, wherever possible.

#### Dependency descriptor

A dependency descriptor makes sure that the class is loaded from the model during runtime.
This allows to add for example circular dependencies between classes.

**Note:** This does not work with Invenio's system fields, as these are handled in
a special way by Invenio and are skipped. For example, `pid` field on a record might
not be created in this way.

```python

class A:
    b = Dependency("B")
```

#### `builder.get_runtime_dependencies()`

This call returns an object that can return resolved dependencies during the runtime via
its `get` method. This is useful for example when you want to access model artefact from
within a function or a method. This can not be used in static initialization.

```python

class MyPreset:
    def apply(self, builder, model, ...):
        runtime_deps = builder.get_runtime_dependencies()
        class A:
            def __init__(self):
                self.b = runtime_deps.get("B")
        yield AddClass("A", A)
```

#### Injected properties

`oarepo_model` and `oarepo_model_namespace` are injected into every generated class. Imported
modules created by the model expose whatever attributes you added via customizations, but do not
receive special injections automatically.

### Early binding (for system fields and similar)

In system fields, due to the nature they are initialized in Invenio, we can not use
late binding. This means that we need to use the classes directly in the system fields
and they have to be built before the system fields are declared. This is done via reordering
the presets and customizations so that the system fields' classes are built before the classes
that use them.

Each preset has two properties: `provides` and `depends_on`. The `provides` property
is a list of classes that the preset provides or modifies, while the `depends_on`
property is a list of classes that the preset depends on. The presets are sorted
by their dependencies, so that the dependencies are built before the preset itself.

You can then get the built dependencies from the 3rd argument of the `apply` method
of the preset. This is a dictionary of classes that were built during the model building process.

Example:

```python

class MyPreset(Preset):
    provides = ["MyClass"]
    depends_on = ["Record"]

    def apply(self, builder, model, dependencies):
        # built_dependencies is a dict of classes that were built during the model building process
        class MyClass(metaclass=MetaThatNeedsToHaveBProperty):
            # 
            b = dependencies["Record"]  # The Record has been built at this point and is a valid class
        yield AddClass("MyClass", MyClass)
```

## Internal

### Adding license headers

```bash
uv pip install licenseheaders

( cd src; licenseheaders -t ../.licenseheaders.tmpl -y 2025 -o "CESNET z.s.p.o" -n oarepo-model -u http://github.com/oarepo/oarepo-model )

```
