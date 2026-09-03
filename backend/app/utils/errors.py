from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class LegalMetrixException(HTTPException):
    """Base exception for LegalMetriX system errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "INTERNAL_ERROR",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.metadata = metadata or {}

class ResourceNotFoundError(LegalMetrixException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found.",
            error_code="RESOURCE_NOT_FOUND"
        )

class InvalidStateTransitionError(LegalMetrixException):
    def __init__(self, current_state: str, target_state: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition state from '{current_state}' to '{target_state}'.",
            error_code="INVALID_STATE_TRANSITION"
        )

class UnauthorizedError(LegalMetrixException):
    def __init__(self, detail: str = "Authentication credentials were invalid or missing."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )

class ForbiddenError(LegalMetrixException):
    def __init__(self, detail: str = "Operation not permitted for current role."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )

class AuditVerificationError(LegalMetrixException):
    def __init__(self, detail: str = "Audit chain integrity verification failed."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="AUDIT_VERIFICATION_FAILED"
        )

class ValidationError(LegalMetrixException):
    def __init__(self, detail: str = "Input or state validation failed."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_FAILED"
        )

