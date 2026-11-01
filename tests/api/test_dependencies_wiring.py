"""PLAN.md FASE 4.1/4.2/4.3 — FastAPI-wired get_db/get_current_user/require_workspace_role."""

from app.core.dependencies import get_current_user, require_workspace_role
from app.core.security import create_access_token, get_jwt_algorithm, get_jwt_secret_key
from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _bearer_token_for(user: User) -> str:
    return create_access_token(
        user_id=str(user.id),
        token_version=user.token_version,
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
        expires_in_seconds=3600,
    )


def test_get_current_user_rejects_missing_authorization_header(db_session: Session) -> None:
    @app.get("/__test/whoami")
    def _whoami(user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"email": user.email}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test/whoami")

    assert response.status_code == 401


def test_get_current_user_accepts_valid_bearer_token(db_session: Session) -> None:
    user = User(email="auditor@example.com", password_hash="h", full_name="A")
    db_session.add(user)
    db_session.commit()

    @app.get("/__test/whoami2")
    def _whoami(user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"email": user.email}

    with TestClient(app) as client:
        response = client.get(
            "/__test/whoami2", headers={"Authorization": f"Bearer {_bearer_token_for(user)}"}
        )

    assert response.status_code == 200
    assert response.json() == {"email": "auditor@example.com"}


def test_require_workspace_role_allows_member_with_permitted_role(db_session: Session) -> None:
    user = User(email="manager@example.com", password_hash="h", full_name="M")
    workspace = Workspace(name="Agensi")
    db_session.add_all([user, workspace])
    db_session.commit()
    db_session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="MANAGER"))
    db_session.commit()

    @app.get("/__test/workspaces/{workspace_id}/guarded")
    def _guarded(
        member: WorkspaceMember = Depends(require_workspace_role({"MANAGER"})),
    ) -> dict[str, str]:
        return {"role": member.role}

    with TestClient(app) as client:
        response = client.get(
            f"/__test/workspaces/{workspace.id}/guarded",
            headers={"Authorization": f"Bearer {_bearer_token_for(user)}"},
        )

    assert response.status_code == 200
    assert response.json() == {"role": "MANAGER"}


def test_require_workspace_role_rejects_non_member(db_session: Session) -> None:
    user = User(email="outsider@example.com", password_hash="h", full_name="O")
    workspace = Workspace(name="Agensi")
    db_session.add_all([user, workspace])
    db_session.commit()

    @app.get("/__test/workspaces/{workspace_id}/guarded2")
    def _guarded(
        member: WorkspaceMember = Depends(require_workspace_role({"MANAGER"})),
    ) -> dict[str, str]:
        return {"role": member.role}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            f"/__test/workspaces/{workspace.id}/guarded2",
            headers={"Authorization": f"Bearer {_bearer_token_for(user)}"},
        )

    assert response.status_code == 403
