# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Exception classes for OARepo model building and processing.

This module defines custom exception classes used throughout the OARepo model
building process, including errors for model building, registration, and
customization application.
"""

from __future__ import annotations


class ModelBuildError(Exception):
    """Exception raised for errors in the model building process."""


class PresetDeclarationWarning(FutureWarning):
    """Warning raised when a preset declares provides/modifies that do not match what it does.

    Subclasses FutureWarning, not DeprecationWarning, because it is shown by default: the
    misdeclared preset is usually in a package the person running the application did not write,
    and DeprecationWarning is hidden unless the code runs in __main__.
    """


class PostBuildMutationWarning(FutureWarning):
    """Warning raised when an already built partial is mutated through its raw containers.

    Such a mutation is silently lost, so the preset that performs it usually misses the partial in
    its `modifies`. Subclasses FutureWarning, not DeprecationWarning, because it is shown by
    default: the offending preset is usually in a package the person running the application did
    not write.
    """


class AlreadyRegisteredError(ModelBuildError):
    """Exception raised when a class is already registered."""


class PartialNotFoundError(ModelBuildError):
    """Exception raised when a class is not found."""


class BaseClassNotFoundError(ModelBuildError):
    """Exception raised when a base class is not found in the model."""


class ApplyCustomizationError(ModelBuildError):
    """Exception raised when applying a customization fails."""


class ClassBuildError(ApplyCustomizationError):
    """Exception raised when building a class fails."""


class ClassListBuildError(ApplyCustomizationError):
    """Exception raised when building a class list fails."""
