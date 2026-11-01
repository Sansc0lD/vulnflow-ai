"""App-raised exceptions mapped to StandardErrorEnvelope — SDD §2.6.1.7."""

from vulnflow_contracts import ErrorCode


class AppError(Exception):
    """Base for every error the global exception handler wraps into
    StandardErrorEnvelope (PLAN.md FASE 4.1)."""

    status_code: int = 500
    error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR


class AuthenticationError(AppError):
    status_code = 401
    error_code = ErrorCode.AUTHENTICATION_FAILED


class PermissionDeniedError(AppError):
    status_code = 403
    error_code = ErrorCode.PERMISSION_DENIED


class QuotaExhaustedError(AppError):
    status_code = 402
    error_code = ErrorCode.QUOTA_EXHAUSTED


class ResourceNotFoundError(AppError):
    status_code = 404
    error_code = ErrorCode.RESOURCE_NOT_FOUND


class BatchLimitExceededError(AppError):
    status_code = 413
    error_code = ErrorCode.BATCH_LIMIT_EXCEEDED


class PayloadTooLargeError(AppError):
    status_code = 413
    error_code = ErrorCode.PAYLOAD_TOO_LARGE


class ValidationFailedError(AppError):
    status_code = 422
    error_code = ErrorCode.VALIDATION_FAILED


class ConflictError(AppError):
    """EC-03 (akun dihapus tanpa transfer ownership) / EC-11 (optimistic lock)."""

    status_code = 409
    error_code = ErrorCode.CONFLICT
