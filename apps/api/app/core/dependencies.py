"""Auth & RBAC dependency logic — PLAN.md FASE 4.1/4.2/4.3.

`authenticate_user`/`ensure_workspace_role` are plain functions (not FastAPI
`Depends`-decorated) so the actual authorization logic is unit-testable
against a real DB session without needing FastAPI's request/response
machinery. `get_db`/`get_current_user`/`require_workspace_role` are the thin
FastAPI wiring around them, used via `Depends(...)` in routers.
"""

import hashlib
import threading
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_database_url, make_engine, make_session_factory
from app.core.database import get_db as _iter_db_session
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token, get_jwt_algorithm, get_jwt_secret_key
from app.models.api_key import APIKey
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember

_bearer_scheme = HTTPBearer(auto_error=False)
_session_factory: sessionmaker[Session] | None = None
_session_factory_lock = threading.Lock()


def authenticate_user(token: str, db: Session, *, secret_key: str, algorithm: str) -> User:
    try:
        payload = decode_access_token(token, secret_key=secret_key, algorithm=algorithm)
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid or expired access token.") from exc

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError as exc:
        raise AuthenticationError("Token subject is not a valid user id.") from exc

    user = db.get(User, user_id)
    if user is None:
        raise AuthenticationError("User not found.")
    if user.status != "ACTIVE":
        raise AuthenticationError("User account is suspended or inactive.")
    if user.token_version != payload.get("token_version"):
        raise AuthenticationError("Token has been revoked.")
    return user


def revoke_user_tokens(user: User, db: Session) -> None:
    """F4-HIGH-03: Increments token_version to immediately revoke all issued JWTs."""
    user.token_version += 1
    db.commit()


def ensure_workspace_role(
    member: WorkspaceMember | None, *, allowed_roles: set[str]
) -> WorkspaceMember:
    if member is None or member.role not in allowed_roles:
        raise PermissionDeniedError("You do not have access to this workspace resource.")
    return member


def workspace_is_active(workspace_id: uuid.UUID, db: Session) -> bool:
    """UC-04 soft delete — `workspaces.is_deleted` is only a real control if
    something reads it. Nothing did, so a soft-deleted workspace stayed fully
    readable and writable for its whole 30-day retention window.
    """
    return (
        db.query(Workspace.id)
        .filter(Workspace.id == workspace_id, Workspace.is_deleted.is_(False))
        .one_or_none()
        is not None
    )


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        with _session_factory_lock:
            if _session_factory is None:
                _session_factory = make_session_factory(make_engine(get_database_url()))
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    yield from _iter_db_session(_get_session_factory())


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationError("Missing bearer token.")
    return authenticate_user(
        credentials.credentials, db, secret_key=get_jwt_secret_key(), algorithm=get_jwt_algorithm()
    )


def require_workspace_role(
    allowed_roles: set[str],
) -> Callable[[uuid.UUID, User, Session], WorkspaceMember]:
    def _dependency(
        workspace_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> WorkspaceMember:
        if not workspace_is_active(workspace_id, db):
            raise PermissionDeniedError("You do not have access to this workspace resource.")
        member = (
            db.query(WorkspaceMember)
            .filter_by(workspace_id=workspace_id, user_id=current_user.id)
            .one_or_none()
        )
        return ensure_workspace_role(member, allowed_roles=allowed_roles)

    return _dependency


def authenticate_api_key(raw_key: str, workspace_id: uuid.UUID, db: Session) -> APIKey:
    """SDD §2.6.1.2 — `X-VulnFlow-API-Key` auth for CLI ingestion endpoints."""
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    api_key = db.query(APIKey).filter_by(key_hash=key_hash).one_or_none()
    if api_key is None or not api_key.is_active or api_key.workspace_id != workspace_id:
        raise AuthenticationError("API key is invalid, inactive, or revoked.")
    if not workspace_is_active(workspace_id, db):
        # Otherwise a CLI agent could keep ingesting findings into a workspace
        # that is soft-deleted and awaiting purge (UC-04).
        raise AuthenticationError("API key is invalid, inactive, or revoked.")

    api_key.last_used_at = datetime.now(UTC)
    db.commit()
    return api_key


def require_api_key(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_vulnflow_api_key: str | None = Header(default=None),
) -> APIKey:
    if not x_vulnflow_api_key:
        raise AuthenticationError("Missing X-VulnFlow-API-Key header.")
    return authenticate_api_key(x_vulnflow_api_key, workspace_id, db)


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superadmin:
        raise PermissionDeniedError("Superadmin privileges required.")
    return current_user
