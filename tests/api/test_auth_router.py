"""PLAN.md FASE 4.2 — AuthRouter (register/login, SDD §2.6.1.4)."""

from app.core.security import create_invitation_token, get_jwt_algorithm, get_jwt_secret_key
from app.main import app
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_VALID_REGISTRATION = {
    "email": "pentester@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Auditor Satu",
    "workspace_name": "Agensi Keamanan Siber",
}


def test_register_creates_user_workspace_subscription_and_returns_token(
    db_session: Session,
) -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=_VALID_REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "pentester@example.com"
    assert body["access_token"]
    assert body["token_type"] == "bearer"

    user = db_session.query(User).filter_by(email="pentester@example.com").one()
    workspace = db_session.query(Workspace).filter_by(name="Agensi Keamanan Siber").one()
    member = db_session.query(WorkspaceMember).filter_by(user_id=user.id).one()
    subscription = db_session.query(Subscription).filter_by(workspace_id=workspace.id).one()
    assert member.role == "MANAGER"
    assert subscription.tier == "FREE"
    assert subscription.monthly_report_quota == 3


def test_register_rejects_duplicate_email(db_session: Session) -> None:
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json=_VALID_REGISTRATION)
        response = client.post("/api/v1/auth/register", json=_VALID_REGISTRATION)

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


def test_register_rejects_weak_password(db_session: Session) -> None:
    payload = {**_VALID_REGISTRATION, "password": "weak"}

    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


def test_register_with_invitation_token_joins_existing_workspace(db_session: Session) -> None:
    workspace = Workspace(name="Workspace Yang Mengundang")
    db_session.add(workspace)
    db_session.commit()
    invitation = create_invitation_token(
        workspace_id=str(workspace.id),
        role="PENTESTER",
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
    )
    payload = {**_VALID_REGISTRATION, "invitation_token": invitation}

    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["workspace_id"] == str(workspace.id)
    user = db_session.query(User).filter_by(email="pentester@example.com").one()
    member = db_session.query(WorkspaceMember).filter_by(user_id=user.id).one()
    assert member.role == "PENTESTER"
    assert member.workspace_id == workspace.id
    # Joining via invitation must not create a second (duplicate) workspace.
    assert db_session.query(Workspace).count() == 1


def test_register_rejects_invalid_invitation_token(db_session: Session) -> None:
    payload = {**_VALID_REGISTRATION, "invitation_token": "not-a-real-token"}

    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 401


def test_login_succeeds_with_correct_credentials(db_session: Session) -> None:
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json=_VALID_REGISTRATION)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": _VALID_REGISTRATION["email"],
                "password": _VALID_REGISTRATION["password"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "pentester@example.com"
    assert len(body["workspaces"]) == 1
    assert body["workspaces"][0]["role"] == "MANAGER"


def test_login_rejects_wrong_password(db_session: Session) -> None:
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json=_VALID_REGISTRATION)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": _VALID_REGISTRATION["email"], "password": "WrongPassword1!"},
        )

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_FAILED"


def test_login_rejects_unknown_email(db_session: Session) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Str0ng!Passw0rd"},
        )

    assert response.status_code == 401


def test_login_rejects_suspended_account(db_session: Session) -> None:
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json=_VALID_REGISTRATION)

    user = db_session.query(User).filter_by(email=_VALID_REGISTRATION["email"]).one()
    user.status = "SUSPENDED"
    db_session.commit()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": _VALID_REGISTRATION["email"],
                "password": _VALID_REGISTRATION["password"],
            },
        )

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


def test_register_rejects_invitation_issued_to_different_email(db_session: Session) -> None:
    # F4-HIGH-11: Token bound to email cannot be used by another email
    workspace = Workspace(name="Workspace Email Bound")
    db_session.add(workspace)
    db_session.commit()
    invitation = create_invitation_token(
        workspace_id=str(workspace.id),
        role="PENTESTER",
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
        email="invited@example.com",
    )
    # Registration attempt with different email
    payload = {
        **_VALID_REGISTRATION,
        "email": "attacker@example.com",
        "invitation_token": invitation,
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 401
    assert "different email address" in response.json()["message"]


def test_register_rejects_replayed_invitation_token(db_session: Session) -> None:
    # F4-HIGH-11: Replaying an already-consumed invitation token is rejected
    workspace = Workspace(name="Workspace Replay Protected")
    db_session.add(workspace)
    db_session.commit()
    invitation = create_invitation_token(
        workspace_id=str(workspace.id),
        role="PENTESTER",
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
        email="member1@example.com",
    )
    payload1 = {
        **_VALID_REGISTRATION,
        "email": "member1@example.com",
        "invitation_token": invitation,
    }

    with TestClient(app) as client:
        # First use succeeds
        resp1 = client.post("/api/v1/auth/register", json=payload1)
        assert resp1.status_code == 201

        # Second use with the same token must be rejected (replay attack)
        payload2 = {
            **_VALID_REGISTRATION,
            "email": "member1@example.com",
            "invitation_token": invitation,
        }
        resp2 = client.post("/api/v1/auth/register", json=payload2)
        assert resp2.status_code in (401, 409)
