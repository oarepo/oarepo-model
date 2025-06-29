class ModelBuildError(Exception):
    """Exception raised for errors in the model building process."""


class AlreadyRegisteredError(ModelBuildError):
    """Exception raised when a class is already registered."""


class PartialNotFoundError(ModelBuildError):
    """Exception raised when a class is not found."""


class BaseClassNotFoundError(ModelBuildError):
    """Exception raised when a base class is not found in the model."""
