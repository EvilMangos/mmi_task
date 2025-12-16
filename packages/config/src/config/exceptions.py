"""Custom exceptions for configuration errors."""


class ConfigurationError(Exception):
    """Base exception for configuration-related errors.

    This exception is provided for external consumers who wish to wrap or
    translate configuration errors. Note that the config package itself raises
    pydantic.ValidationError for invalid settings; this exception can be used
    by application code to provide a unified error type if desired.
    """
