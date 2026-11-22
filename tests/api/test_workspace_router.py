"""PLAN.md FASE 4.3 — WorkspaceRouter (UC-04, UC-05, UC-03; SDD §2.4.2)."""

import uuid

from app.main import app
from app.models.api_key import APIKey
from app.models.workspace_member import WorkspaceMember
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_REGISTRATION = {
    "email": "manager@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Manager Satu",
    "workspace_name": "Agensi Awal",
}


def _register_and_get_token(client: TestClient) -> tuple[str, str]:
    response = client.post("/api/v1/auth/register", json=_REGISTRATION)
    body = response.json()
    return body["access_token"], body["workspace_id"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace_makes_caller_manager(db_session: Session) -> None:
    from app.models.subscription import Subscription

    with TestClient(app) as client:
        token, first_ws_id = _register_and_get_token(client)
        first_sub = (
            db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(first_ws_id)).one()
        )
        first_sub.tier = "PRO"
        db_session.commit()

        response = client.post(
            "/api/v1/workspaces", json={"name": "Agensi Kedua"}, headers=_auth_headers(token)
        )

    assert response.status_code == 201
    workspace_id = uuid.UUID(response.json()["id"])
    member = db_session.query(WorkspaceMember).filter_by(workspace_id=workspace_id).one()
    assert member.role == "MANAGER"


def test_create_workspace_rejects_second_free_workspace(db_session: Session) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_get_token(client)
        resp = client.post(
            "/api/v1/workspaces",
            json={"name": "Second Free WS"},
            headers=_auth_headers(token),
        )

    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_FAILED"
    assert "Free-tier workspace" in resp.json()["message"]


def test_invited_viewer_can_create_one_personal_free_workspace(db_session: Session) -> None:
    with TestClient(app) as client:
        mgr_token, ws_id = _register_and_get_token(client)
        invite_resp = client.post(
            f"/api/v1/workspaces/{ws_id}/members",
            json={"email": "viewer-creator@example.com", "role": "VIEWER"},
            headers=_auth_headers(mgr_token),
        )
        inv_token = invite_resp.json()["invitation_token"]
        viewer_reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "viewer-creator@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer Creator",
                "workspace_name": "Unused",
                "invitation_token": inv_token,
            },
        )
        viewer_token = viewer_reg.json()["access_token"]

        # 1st personal FREE workspace succeeds with MANAGER role; original workspace stays VIEWER
        created = client.post(
            "/api/v1/workspaces",
            json={"name": "Viewer Personal Lab"},
            headers=_auth_headers(viewer_token),
        )
        assert created.status_code == 201
        created_ws_id = uuid.UUID(created.json()["id"])
        membership = db_session.query(WorkspaceMember).filter_by(workspace_id=created_ws_id).one()
        assert membership.role == "MANAGER"

        # 2nd personal FREE workspace is rejected
        second = client.post(
            "/api/v1/workspaces",
            json={"name": "Viewer Second Free"},
            headers=_auth_headers(viewer_token),
        )
        assert second.status_code == 422
        assert "Free-tier workspace" in second.json()["message"]


def test_create_workspace_requires_authentication(db_session: Session) -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/workspaces", json={"name": "X"})

    assert response.status_code == 401


def test_update_workspace_allows_manager(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"brand_primary_color": "#112233"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 200
    assert response.json()["brand_primary_color"] == "#112233"


def test_update_workspace_rejects_non_member(db_session: Session) -> None:
    with TestClient(app) as client:
        _, workspace_id = _register_and_get_token(client)
        outsider_registration = {**_REGISTRATION, "email": "outsider@example.com"}
        other_token = client.post("/api/v1/auth/register", json=outsider_registration).json()[
            "access_token"
        ]
        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Hijacked"},
            headers=_auth_headers(other_token),
        )

    assert response.status_code == 403


def test_invite_member_returns_signed_invitation_token(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "invitee@example.com", "role": "PENTESTER"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["invitation_token"]
    assert body["expires_in"] == 7 * 24 * 3600


def test_create_api_key_returns_raw_key_once(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"label": "CI Runner"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["api_key"].startswith("vf_live_")

    stored = db_session.query(APIKey).filter_by(label="CI Runner").one()
    assert stored.key_hash != body["api_key"]  # only the hash is persisted


def test_create_api_key_rejects_non_manager(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)

        invite_response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "viewer@example.com", "role": "VIEWER"},
            headers=_auth_headers(token),
        )
        invitation_token = invite_response.json()["invitation_token"]
        viewer_registration = {
            "email": "viewer@example.com",
            "password": "Str0ng!Passw0rd",
            "full_name": "Viewer Satu",
            "workspace_name": "Unused",
            "invitation_token": invitation_token,
        }
        viewer_token = client.post("/api/v1/auth/register", json=viewer_registration).json()[
            "access_token"
        ]

        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"label": "Should Fail"},
            headers=_auth_headers(viewer_token),
        )

    assert response.status_code == 403


def test_workspace_not_found_returns_404(db_session: Session) -> None:
    import uuid

    with TestClient(app) as client:
        token, _ = _register_and_get_token(client)
        response = client.patch(
            f"/api/v1/workspaces/{uuid.uuid4()}",
            json={"name": "X"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 403  # not a member of a workspace that doesn't exist either


def test_create_workspace_enforces_limit_per_user(db_session: Session) -> None:
    # F4-LOW-15: Maximum 5 owned workspaces per user (after upgrading prior FREE workspaces)
    from app.models.subscription import Subscription

    with TestClient(app) as client:
        token, first_ws_id = _register_and_get_token(client)
        sub = db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(first_ws_id)).one()
        sub.tier = "PRO"
        db_session.commit()

        # 1st workspace already created at register. Create 4 more -> total 5
        for i in range(2, 6):
            resp = client.post(
                "/api/v1/workspaces",
                json={"name": f"Workspace {i}"},
                headers=_auth_headers(token),
            )
            assert resp.status_code == 201
            created_id = uuid.UUID(resp.json()["id"])
            created_sub = db_session.query(Subscription).filter_by(workspace_id=created_id).one()
            created_sub.tier = "PRO"
            db_session.commit()

        # 6th workspace attempt must be rejected
        overflow_resp = client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace 6"},
            headers=_auth_headers(token),
        )
        assert overflow_resp.status_code == 422
        assert overflow_resp.json()["code"] == "VALIDATION_FAILED"
        assert "more than 5 workspaces" in overflow_resp.json()["message"]


def test_workspace_crud_members_invitations_pentester_keys_logo_and_audit(
    db_session: Session,
) -> None:
    import base64
    import io
    from datetime import UTC, datetime, timedelta

    from app.models.subscription import Subscription
    from app.routers.workspaces import get_upload_storage
    from PIL import Image

    class _FakeStorage:
        def __init__(self) -> None:
            self.uploaded: dict[str, bytes] = {}

        def upload_bytes(self, key: str, data: bytes, *, content_type: str = "image/png") -> None:
            self.uploaded[key] = data

        def generate_presigned_url(self, key: str, *, expires_in_seconds: int) -> str:
            return f"https://minio.local/{key}?exp={expires_in_seconds}"

    fake_storage = _FakeStorage()
    app.dependency_overrides[get_upload_storage] = lambda: fake_storage
    try:
        with TestClient(app) as client:
            mgr_token, ws_id = _register_and_get_token(client)
            mgr_headers = _auth_headers(mgr_token)

            assert len(client.get("/api/v1/workspaces", headers=mgr_headers).json()) == 1
            ws_detail = client.get(f"/api/v1/workspaces/{ws_id}", headers=mgr_headers)
            assert ws_detail.status_code == 200

            # Invite and accept as an existing user
            p2 = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing-pentester@example.com",
                    "password": "Str0ng!Passw0rd",
                    "full_name": "Existing Pentester",
                    "workspace_name": "Own WS",
                },
            ).json()
            p2_headers = _auth_headers(p2["access_token"])

            inv_token = client.post(
                f"/api/v1/workspaces/{ws_id}/members",
                headers=mgr_headers,
                json={"email": "existing-pentester@example.com", "role": "PENTESTER"},
            ).json()["invitation_token"]

            accepted = client.post(
                "/api/v1/workspaces/invitations/accept",
                headers=p2_headers,
                json={"invitation_token": inv_token},
            )
            assert accepted.status_code == 200
            assert accepted.json()["role"] == "PENTESTER"

            members = client.get(f"/api/v1/workspaces/{ws_id}/members", headers=p2_headers).json()
            assert len(members) == 2

            # EC-03: sole manager cannot be demoted or removed
            mgr_uid = [m["user_id"] for m in members if m["role"] == "MANAGER"][0]
            assert (
                client.patch(
                    f"/api/v1/workspaces/{ws_id}/members/{mgr_uid}",
                    headers=mgr_headers,
                    json={"role": "PENTESTER"},
                ).status_code
                == 409
            )
            assert (
                client.delete(
                    f"/api/v1/workspaces/{ws_id}/members/{mgr_uid}",
                    headers=mgr_headers,
                ).status_code
                == 409
            )

            # PENTESTER can create/list/revoke own API keys up to max 5; cannot revoke mgr key
            mgr_key = client.post(
                f"/api/v1/workspaces/{ws_id}/api-keys",
                headers=mgr_headers,
                json={"label": "Mgr Key"},
            ).json()
            pentester_keys = []
            for idx in range(5):
                k_resp = client.post(
                    f"/api/v1/workspaces/{ws_id}/api-keys",
                    headers=p2_headers,
                    json={"label": f"Key {idx}"},
                )
                assert k_resp.status_code == 201
                pentester_keys.append(k_resp.json()["id"])
            assert (
                client.post(
                    f"/api/v1/workspaces/{ws_id}/api-keys",
                    headers=p2_headers,
                    json={"label": "Key 6"},
                ).status_code
                == 422
            )
            assert (
                len(client.get(f"/api/v1/workspaces/{ws_id}/api-keys", headers=p2_headers).json())
                == 5
            )
            assert (
                client.delete(
                    f"/api/v1/workspaces/{ws_id}/api-keys/{mgr_key['id']}",
                    headers=p2_headers,
                ).status_code
                == 403
            )
            assert (
                client.delete(
                    f"/api/v1/workspaces/{ws_id}/api-keys/{pentester_keys[0]}",
                    headers=p2_headers,
                ).status_code
                == 200
            )

            # Logo upload blocked on FREE tier, succeeds on PRO
            buf = io.BytesIO()
            Image.new("RGB", (20, 20), (10, 20, 30)).save(buf, format="PNG")
            png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            assert (
                client.post(
                    f"/api/v1/workspaces/{ws_id}/logo",
                    headers=mgr_headers,
                    json={
                        "filename": "logo.png",
                        "content_type": "image/png",
                        "data_base64": png_b64,
                    },
                ).status_code
                == 403
            )
            sub = db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(ws_id)).one()
            sub.tier = "PRO"
            db_session.commit()
            logo_ok = client.post(
                f"/api/v1/workspaces/{ws_id}/logo",
                headers=mgr_headers,
                json={"filename": "logo.png", "content_type": "image/png", "data_base64": png_b64},
            )
            assert logo_ok.status_code == 200
            assert "logo.png" in logo_ok.json()["storage_path"]

            # Delete workspace blocked when active project exists, succeeds once archived
            proj = client.post(
                f"/api/v1/workspaces/{ws_id}/projects",
                headers=mgr_headers,
                json={
                    "name": "P",
                    "client_name": "C",
                    "target_scope": ["a.com"],
                    "roe_start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                    "roe_end_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
                },
            ).json()
            assert (
                client.request(
                    "DELETE",
                    f"/api/v1/workspaces/{ws_id}",
                    headers=mgr_headers,
                    json={
                        "password": _REGISTRATION["password"],
                        "confirm_workspace_name": "Agensi Awal",
                    },
                ).status_code
                == 409
            )
            client.patch(
                f"/api/v1/workspaces/{ws_id}/projects/{proj['id']}",
                headers=mgr_headers,
                json={"status": "ARCHIVED"},
            )
            assert (
                client.request(
                    "DELETE",
                    f"/api/v1/workspaces/{ws_id}",
                    headers=mgr_headers,
                    json={
                        "password": _REGISTRATION["password"],
                        "confirm_workspace_name": "Agensi Awal",
                    },
                ).status_code
                == 200
            )
            assert client.get("/api/v1/workspaces", headers=mgr_headers).json() == []
    finally:
        app.dependency_overrides.pop(get_upload_storage, None)
