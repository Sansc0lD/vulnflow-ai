"""PLAN.md FASE 4.1 — app-raised exceptions mapped to StandardErrorEnvelope (SDD §2.6.1.7)."""

from app.core.exceptions import (
    AuthenticationError,
    BatchLimitExceededError,
    ConflictError,
    PermissionDeniedError,
    QuotaExhaustedError,
    ResourceNotFoundError,
    ValidationFailedError,
)

from vulnflow_contracts import ErrorCode


def test_authentication_error_maps_to_401() -> None:
    error = AuthenticationError("bad token")
    assert error.status_code == 401
    assert error.error_code == ErrorCode.AUTHENTICATION_FAILED
    assert str(error) == "bad token"


def test_permission_denied_error_maps_to_403() -> None:
    assert PermissionDeniedError("no access").status_code == 403
    assert PermissionDeniedError("no access").error_code == ErrorCode.PERMISSION_DENIED


def test_quota_exhausted_error_maps_to_402() -> None:
    assert QuotaExhaustedError("quota used up").status_code == 402
    assert QuotaExhaustedError("quota used up").error_code == ErrorCode.QUOTA_EXHAUSTED


def test_resource_not_found_error_maps_to_404() -> None:
    assert ResourceNotFoundError("not found").status_code == 404
    assert ResourceNotFoundError("not found").error_code == ErrorCode.RESOURCE_NOT_FOUND


def test_batch_limit_exceeded_error_maps_to_413() -> None:
    assert BatchLimitExceededError("too many").status_code == 413
    assert BatchLimitExceededError("too many").error_code == ErrorCode.BATCH_LIMIT_EXCEEDED


def test_validation_failed_error_maps_to_422() -> None:
    assert ValidationFailedError("bad input").status_code == 422
    assert ValidationFailedError("bad input").error_code == ErrorCode.VALIDATION_FAILED


def test_conflict_error_maps_to_409() -> None:
    # EC-03 / EC-11
    assert ConflictError("version mismatch").status_code == 409
    assert ConflictError("version mismatch").error_code == ErrorCode.CONFLICT
