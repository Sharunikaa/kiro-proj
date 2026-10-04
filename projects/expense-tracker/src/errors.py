"""Domain errors raised by the service layer and mapped to HTTP by routes.

- NotFoundError        -> HTTP 404
- DomainValidationError -> HTTP 422
"""

from __future__ import annotations


class NotFoundError(Exception):
    """Raised when a referenced entity does not exist (maps to 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)
        self.message = message


class DomainValidationError(Exception):
    """Raised on a semantic/business-rule violation (maps to 422)."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message)
        self.message = message
