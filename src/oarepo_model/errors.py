#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
class ModelBuildError(Exception):
    """Exception raised for errors in the model building process."""


class AlreadyRegisteredError(ModelBuildError):
    """Exception raised when a class is already registered."""


class PartialNotFoundError(ModelBuildError):
    """Exception raised when a class is not found."""


class BaseClassNotFoundError(ModelBuildError):
    """Exception raised when a base class is not found in the model."""
