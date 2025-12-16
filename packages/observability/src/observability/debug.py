"""Debug mode detection utilities."""

import os


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via the DEBUG environment variable.

    Truthy values are: "1", "true", "yes" (case-insensitive).
    Returns False if DEBUG is not set or has any other value.
    """
    debug_value = os.environ.get("DEBUG", "").lower()
    return debug_value in ("1", "true", "yes")
