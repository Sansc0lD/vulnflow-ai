"""AuthRouter — PLAN.md FASE 4.2 (SDD §2.6.1.4, UC-01/UC-02)."""

import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import SYSTEM_WORKSPACE_ID, get_client_ip, record_audit_log
from app.core.dependencies import (
    get_current_user,
    get_db,
    revoke_user_tokens,
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    MFARequiredError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_invitation_token,
    decode_password_reset_token,
    extract_unverified_reset_user_id,
    get_jwt_algorithm,
    get_jwt_expires_in_seconds,
    get_jwt_secret_key,
    hash_password,
    mark_invitation_used,
    verify_password,
)
from app.core.totp import build_otpauth_uri, generate_totp_secret, verify_totp
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.services.email_service import EmailSender, get_email_sender, send_password_reset_email
from vulnflow_contracts import (
    DeleteAccountRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MeResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
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
) -> tuple[Workspace, str, str | None, int]:
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
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("The invited workspace no longer exists.")

    jti_raw = invite.get("jti")
    jti = str(jti_raw) if jti_raw else None
    exp = int(invite.get("exp", int(time.time()) + 7 * 24 * 3600))
    return workspace, str(invite["role"]), jti, exp


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
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    if db.query(User).filter_by(email=payload.email).one_or_none() is not None:
        raise ConflictError("An account with this email already exists.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    invite_jti: str | None = None
    invite_exp = 0
    if payload.invitation_token:
        workspace, role, invite_jti, invite_exp = _join_workspace_via_invitation(
            db, payload.invitation_token, payload.email
        )
    else:
        workspace, role = _create_default_workspace(db, payload.workspace_name)

    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role))
    db.flush()
    record_audit_log(
        db,
        workspace_id=workspace.id,
        actor_user_id=user.id,
        action="USER_REGISTERED",
        target_entity=f"user:{user.id}",
        ip_address=get_client_ip(request),
        details={"email": user.email, "via_invitation": bool(payload.invitation_token)},
    )
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

    if invite_jti:
        mark_invitation_used(invite_jti, invite_exp)

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
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter_by(email=payload.email).one_or_none()
    password_hash = user.password_hash if user is not None else _TIMING_SAFE_DUMMY_HASH
    password_is_valid = verify_password(payload.password, password_hash)

    if user is None or not password_is_valid:
        raise AuthenticationError("Invalid email or password.")
    if user.status != "ACTIVE":
        raise PermissionDeniedError("This account has been suspended.")

    if user.totp_secret:
        if payload.totp_code is None:
            raise MFARequiredError("Multi-factor authentication code is required.")
        if not verify_totp(user.totp_secret, payload.totp_code):
            raise AuthenticationError("Invalid email, password, or authentication code.")

    memberships = (
        db.query(WorkspaceMember, Workspace, Subscription)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .outerjoin(Subscription, Subscription.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user.id, Workspace.is_deleted.is_(False))
        .all()
    )
    audit_workspace_id = memberships[0][1].id if memberships else SYSTEM_WORKSPACE_ID
    record_audit_log(
        db,
        workspace_id=audit_workspace_id,
        actor_user_id=user.id,
        action="USER_LOGIN",
        target_entity=f"user:{user.id}",
        ip_address=get_client_ip(request),
        details={"is_superadmin": user.is_superadmin},
    )
    db.commit()

    access_token, expires_in = _issue_access_token(user)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserDTO(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_superadmin=user.is_superadmin,
            mfa_enabled=bool(user.totp_secret),
        ),
        workspaces=[
            WorkspaceMembership(
                id=str(workspace.id),
                name=workspace.name,
                role=WorkspaceRole(member.role),
                tier=sub.tier if sub is not None else None,
            )
            for member, workspace, sub in memberships
        ],
    )


def _active_user_dto(user: User) -> UserDTO:
    return UserDTO(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_superadmin=user.is_superadmin,
        mfa_enabled=bool(user.totp_secret),
    )


@router.get("/me", response_model=MeResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    memberships = (
        db.query(WorkspaceMember, Workspace, Subscription)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .outerjoin(Subscription, Subscription.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == current_user.id, Workspace.is_deleted.is_(False))
        .all()
    )
    return MeResponse(
        user=_active_user_dto(current_user),
        workspaces=[
            WorkspaceMembership(
                id=str(workspace.id),
                name=workspace.name,
                role=WorkspaceRole(member.role),
                tier=sub.tier if sub is not None else None,
            )
            for member, workspace, sub in memberships
        ],
    )


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    revoke_user_tokens(current_user, db)
    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=current_user.id,
        action="USER_LOGOUT",
        target_entity=f"user:{current_user.id}",
        ip_address=get_client_ip(request),
        details={},
    )
    db.commit()
    return {"status": "LOGGED_OUT"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> ForgotPasswordResponse:
    user = db.query(User).filter_by(email=payload.email).one_or_none()
    if user is not None and user.status == "ACTIVE":
        reset_token = create_password_reset_token(
            user_id=str(user.id),
            password_hash=user.password_hash,
            secret_key=get_jwt_secret_key(),
            algorithm=get_jwt_algorithm(),
            expires_in_seconds=900,
        )
        send_password_reset_email(email_sender, to_email=user.email, reset_token=reset_token)
        record_audit_log(
            db,
            workspace_id=SYSTEM_WORKSPACE_ID,
            actor_user_id=user.id,
            action="PASSWORD_RESET_REQUESTED",
            target_entity=f"user:{user.id}",
            ip_address=get_client_ip(request),
            details={"email": user.email},
        )
        db.commit()

    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        user_id_str = extract_unverified_reset_user_id(payload.token)
        user_uuid = uuid.UUID(user_id_str)
    except (pyjwt.InvalidTokenError, ValueError) as exc:
        raise AuthenticationError("Password reset token is invalid or expired.") from exc

    user = db.get(User, user_uuid)
    if user is None or user.status != "ACTIVE":
        raise AuthenticationError("Password reset token is invalid or expired.")

    try:
        decode_password_reset_token(
            payload.token,
            password_hash=user.password_hash,
            secret_key=get_jwt_secret_key(),
            algorithm=get_jwt_algorithm(),
        )
    except pyjwt.InvalidTokenError as exc:
        raise AuthenticationError("Password reset token is invalid or expired.") from exc

    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=user.id,
        action="PASSWORD_RESET_COMPLETED",
        target_entity=f"user:{user.id}",
        ip_address=get_client_ip(request),
        details={},
    )
    db.commit()
    return {"status": "PASSWORD_RESET"}


@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MFASetupResponse:
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=current_user.id,
        action="MFA_ENABLED",
        target_entity=f"user:{current_user.id}",
        ip_address=get_client_ip(request),
        details={},
    )
    db.commit()
    return MFASetupResponse(
        secret=secret,
        otpauth_uri=build_otpauth_uri(secret, email=current_user.email),
        enabled=True,
    )


@router.post("/mfa/verify")
def verify_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not current_user.totp_secret:
        raise ValidationFailedError("MFA is not configured for this account.")
    if not verify_totp(current_user.totp_secret, payload.totp_code):
        raise AuthenticationError("Invalid authentication code.")
    return {"valid": True}


@router.delete("/me")
def delete_my_account(
    payload: DeleteAccountRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(payload.password, current_user.password_hash):
        raise AuthenticationError("Invalid password.")

    manager_memberships = (
        db.query(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role == "MANAGER",
            Workspace.is_deleted.is_(False),
        )
        .all()
    )
    for _member, workspace in manager_memberships:
        other_managers = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.role == "MANAGER",
                WorkspaceMember.user_id != current_user.id,
            )
            .count()
        )
        if other_managers == 0:
            raise ConflictError(
                "Cannot delete account while you are the sole MANAGER of an active workspace."
            )

    db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).delete()
    current_user.status = "SUSPENDED"
    current_user.email = f"deleted-{current_user.id}@deleted.vulnflow.local"
    current_user.full_name = "Deleted User"
    current_user.totp_secret = None
    current_user.token_version += 1
    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=current_user.id,
        action="USER_ACCOUNT_DELETED",
        target_entity=f"user:{current_user.id}",
        ip_address=get_client_ip(request),
        details={},
    )
    db.commit()
    return {"status": "ACCOUNT_DELETED"}
