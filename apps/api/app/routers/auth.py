"""AuthRouter — PLAN.md FASE 4.2 (SDD §2.6.1.4, UC-01/UC-02)."""

import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.core.security import (
    create_access_token,
    decode_invitation_token,
    get_jwt_algorithm,
    get_jwt_expires_in_seconds,
    get_jwt_secret_key,
    hash_password,
    mark_invitation_used,
    verify_password,
)
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserDTO,
    WorkspaceMembership,
    WorkspaceRole,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

FREE_TIER_MONTHLY_REPORT_QUOTA = 3
# Avoids a user-enumeration timing side-channel: hashing takes the same time
# whether or not the email exists, since we always run Argon2id verify once.
_TIMING_SAFE_DUMMY_HASH = hash_password("timing-attack-mitigation-dummy-password")


def _issue_access_token(user: User) -> tuple[str, int]:
    expires_in = get_jwt_expires_in_seconds()
    token = create_access_token(
        user_id=str(user.id),
        token_version=user.token_version,
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
        expires_in_seconds=expires_in,
    )
    return token, expires_in


def _join_workspace_via_invitation(
    db: Session, invitation_token: str, registering_email: str
) -> tuple[Workspace, str]:
    try:
        invite = decode_invitation_token(
            invitation_token, secret_key=get_jwt_secret_key(), algorithm=get_jwt_algorithm()
        )
    except pyjwt.InvalidTokenError as exc:
        raise AuthenticationError("Invitation token is invalid or expired.") from exc

    # F4-HIGH-11: verify invitation was issued for this email
    token_email = invite.get("email", "")
    if token_email and token_email.lower() != registering_email.lower():
        raise AuthenticationError("Invitation token was issued for a different email address.")

    workspace = db.get(Workspace, uuid.UUID(invite["workspace_id"]))
    if workspace is None:
        raise ResourceNotFoundError("The invited workspace no longer exists.")

    # F4-HIGH-11: single-use enforcement: mark token jti as used
    jti = invite.get("jti")
    exp = int(invite.get("exp", int(time.time()) + 7 * 24 * 3600))
    if jti:
        mark_invitation_used(jti, exp)

    return workspace, invite["role"]


def _create_default_workspace(db: Session, workspace_name: str) -> tuple[Workspace, str]:
    workspace = Workspace(name=workspace_name)
    db.add(workspace)
    db.flush()
    db.add(
        Subscription(
            workspace_id=workspace.id,
            tier="FREE",
            monthly_report_quota=FREE_TIER_MONTHLY_REPORT_QUOTA,
            quota_reset_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
    return workspace, "MANAGER"


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    if db.query(User).filter_by(email=payload.email).one_or_none() is not None:
        raise ConflictError("An account with this email already exists.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    if payload.invitation_token:
        workspace, role = _join_workspace_via_invitation(
            db, payload.invitation_token, payload.email
        )
    else:
        workspace, role = _create_default_workspace(db, payload.workspace_name)

    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role))
    try:
        db.commit()
    except IntegrityError as exc:
        # The pre-check above is a fast path, not a lock: two concurrent
        # registrations for the same email can both pass it and both reach
        # this commit (`users.email` plain unique index, or `uq_users_email_lower`
        # for a same-mailbox different-casing race). Whichever commits second
        # must get a clean 409, not a raw IntegrityError bubbling to 500.
        db.rollback()
        raise ConflictError("An account with this email already exists.") from exc

    access_token, expires_in = _issue_access_token(user)
    return RegisterResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        workspace_id=str(workspace.id),
        access_token=access_token,
        expires_in=expires_in,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter_by(email=payload.email).one_or_none()
    password_hash = user.password_hash if user is not None else _TIMING_SAFE_DUMMY_HASH
    password_is_valid = verify_password(payload.password, password_hash)

    if user is None or not password_is_valid:
        raise AuthenticationError("Invalid email or password.")
    if user.status == "SUSPENDED":
        raise PermissionDeniedError("This account has been suspended.")

    access_token, expires_in = _issue_access_token(user)
    memberships = (
        db.query(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == user.id)
        .all()
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserDTO(id=str(user.id), email=user.email, full_name=user.full_name),
        workspaces=[
            WorkspaceMembership(
                id=str(workspace.id), name=workspace.name, role=WorkspaceRole(member.role)
            )
            for member, workspace in memberships
        ],
    )
