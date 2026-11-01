"""AIRouter — PLAN.md FASE 4.6 (SDD §2.6.1.3, UC-11; EC-13/EC-14)."""

import os
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.domain.ai_ghostwriter import LLMAdapter, generate_ai_narrative
from app.models.ai_narrative import AINarrative
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace_member import WorkspaceMember
from app.services.gemini_adapter import GeminiLLMAdapter
from vulnflow_contracts import AINarrativeRequest, AINarrativeResponse

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/projects/{project_id}/reports", tags=["ai"]
)

_require_requester_role = require_workspace_role({"MANAGER", "PENTESTER"})


def get_llm_adapter() -> LLMAdapter:
    """Default (production) adapter. Routers depend on this indirection so
    tests can override it with a fake — never hitting the real Gemini API."""
    return GeminiLLMAdapter(
        api_key=os.environ.get("GEMINI_API_KEY", ""),
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        client=httpx.Client(timeout=30.0),
    )


@router.post("/ai-narratives", response_model=AINarrativeResponse)
def generate_narrative_for_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: AINarrativeRequest,
    db: Session = Depends(get_db),
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
    _member: WorkspaceMember = Depends(_require_requester_role),
) -> AINarrativeResponse:
    # F4-CRIT-02: Validate that project belongs to this workspace
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    # F4-MED-16: Catch invalid UUID format from client input
    try:
        finding_ids = [uuid.UUID(fid) for fid in payload.finding_ids]
    except ValueError as exc:
        raise ValidationFailedError(f"Invalid UUID in finding_ids: {exc}") from exc

    findings = (
        db.query(Finding)
        .filter(Finding.project_id == project_id, Finding.id.in_(finding_ids))
        .all()
    )
    if len(findings) != len(finding_ids):
        raise ResourceNotFoundError("One or more findings were not found in this project.")

    content, tokens_consumed, is_fallback = generate_ai_narrative(
        findings, tone=payload.tone, language=payload.language, llm_adapter=llm_adapter
    )

    db.add(
        AINarrative(
            project_id=project_id,
            executive_summary=content.executive_summary,
            business_impact=content.business_impact,
            remediation_priorities=[r.model_dump() for r in content.remediations],
            tokens_consumed=tokens_consumed,
            is_fallback=is_fallback,
        )
    )
    db.commit()

    return AINarrativeResponse(
        narratives=content,
        tokens_consumed=tokens_consumed,
        generated_at=datetime.now(UTC),
        is_fallback=is_fallback,
    )
