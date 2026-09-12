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
