"""PLAN.md FASE 2.3 — Tabel `workspaces` (SDD §2.4.2 #2)."""

from app.models.workspace import Workspace
from sqlalchemy.orm import Session


def test_create_workspace_applies_brand_color_defaults(session: Session) -> None:
    workspace = Workspace(name="Agensi Keamanan Siber")
    session.add(workspace)
    session.commit()

    assert workspace.id is not None
    assert workspace.brand_primary_color == "#0F172A"
    assert workspace.brand_secondary_color == "#3B82F6"
    assert workspace.is_deleted is False
    assert workspace.custom_logo_url is None
