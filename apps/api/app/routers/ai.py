"""AIRouter — PLAN.md FASE 4.6 (SDD §2.6.1.3, UC-11; EC-13/EC-14)."""

import os
import uuid
from collections.abc import Generator
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends, Request
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.audit import get_client_ip, record_audit_log
from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.core.redis_client import get_optional_redis_client
from app.domain.ai_ghostwriter import (
    LLMAdapter,
    _build_fallback_narrative,
    generate_ai_narrative,
)
from app.domain.sanitizer import sanitize_html_text
from app.domain.telemetry import compute_ai_telemetry, get_monthly_spend_ceiling_usd
from app.models.ai_narrative import AINarrative
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace_member import WorkspaceMember
from app.services.gemini_adapter import GeminiLLMAdapter
from vulnflow_contracts import (
    AINarrativeRequest,
    AINarrativeResponse,
    NarrativeContent,
    RemediationItem,
    UpdateAINarrativeRequest,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/projects/{project_id}/reports", tags=["ai"]
)

_require_requester_role = require_workspace_role({"MANAGER", "PENTESTER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})


def get_llm_adapter() -> Generator[LLMAdapter, None, None]:
    """Default (production) adapter. Routers depend on this indirection so
    tests can override it with a fake — never hitting the real Gemini API."""
    with httpx.Client(timeout=45.0) as client:
        yield GeminiLLMAdapter(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model=os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview"),
            client=client,
        )


def _narrative_to_response(narrative: AINarrative) -> AINarrativeResponse:
    approval: Literal["DRAFT", "APPROVED"] = (
        "APPROVED" if narrative.approval_status == "APPROVED" else "DRAFT"
    )
    return AINarrativeResponse(
        id=str(narrative.id),
        approval_status=approval,
        narratives=NarrativeContent(
            executive_summary=narrative.executive_summary,
            business_impact=narrative.business_impact,
            remediations=[
                RemediationItem(**item) for item in (narrative.remediation_priorities or [])
            ],
        ),
        tokens_consumed=narrative.tokens_consumed,
        generated_at=narrative.generated_at,
        is_fallback=narrative.is_fallback,
    )


@router.get("/ai-narratives", response_model=list[AINarrativeResponse])
def list_ai_narratives(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> list[AINarrativeResponse]:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    narratives = (
        db.query(AINarrative)
        .filter_by(project_id=project_id)
        .order_by(AINarrative.generated_at.desc())
        .all()
    )
    return [_narrative_to_response(n) for n in narratives]


@router.post("/ai-narratives", response_model=AINarrativeResponse)
def generate_narrative_for_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: AINarrativeRequest,
    request: Request,
    db: Session = Depends(get_db),
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
    redis_client: Any | None = Depends(get_optional_redis_client),
    current_member: WorkspaceMember = Depends(_require_requester_role),
) -> AINarrativeResponse:
    # F4-CRIT-02: Validate that project belongs to this workspace
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    # F4-MED-16: Catch invalid UUID format from client input
    try:
        parsed_ids = [uuid.UUID(fid) for fid in payload.finding_ids]
    except ValueError as exc:
        raise ValidationFailedError(f"Invalid UUID in finding_ids: {exc}") from exc

    finding_ids = list(dict.fromkeys(parsed_ids))
    findings = (
        db.query(Finding)
        .filter(Finding.project_id == project_id, Finding.id.in_(finding_ids))
        .all()
    )
    if len(findings) != len(finding_ids):
        raise ResourceNotFoundError("One or more findings were not found in this project.")

    if any(f.is_quarantined or f.status == "FALSE_POSITIVE" for f in findings):
        raise ValidationFailedError(
            "Quarantined or FALSE_POSITIVE findings cannot be included in AI narratives."
        )

    try:
        ceiling = get_monthly_spend_ceiling_usd(redis_client)
    except (RedisError, OSError):
        ceiling = get_monthly_spend_ceiling_usd(None)
    telemetry = compute_ai_telemetry(db, spend_ceiling_usd=ceiling)

    if telemetry.circuit_breaker_active:
        content = _build_fallback_narrative(findings)
        tokens_consumed = 0
        is_fallback = True
    else:
        content, tokens_consumed, is_fallback = generate_ai_narrative(
            findings, tone=payload.tone, language=payload.language, llm_adapter=llm_adapter
        )

    narrative = AINarrative(
        project_id=project_id,
        executive_summary=content.executive_summary,
        business_impact=content.business_impact,
        remediation_priorities=[r.model_dump() for r in content.remediations],
        tokens_consumed=tokens_consumed,
        is_fallback=is_fallback,
    )
    db.add(narrative)
    db.flush()
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="AI_NARRATIVE_GENERATED",
        target_entity=f"ai_narrative:{narrative.id}",
        ip_address=get_client_ip(request),
        details={
            "project_id": str(project_id),
            "tokens_consumed": tokens_consumed,
            "is_fallback": is_fallback,
            "findings_count": len(findings),
        },
    )
    db.commit()
    db.refresh(narrative)
    return _narrative_to_response(narrative)


@router.put("/ai-narratives/{narrative_id}", response_model=AINarrativeResponse)
def update_ai_narrative(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    narrative_id: uuid.UUID,
    payload: UpdateAINarrativeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_requester_role),
) -> AINarrativeResponse:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    narrative = (
        db.query(AINarrative).filter_by(id=narrative_id, project_id=project_id).one_or_none()
    )
    if narrative is None:
        raise ResourceNotFoundError("AI narrative not found in this project.")

    clean_remediations = [
        RemediationItem(
            cwe_id=item.cwe_id,
            vuln_title=sanitize_html_text(item.vuln_title),
            remediation_guidance=sanitize_html_text(item.remediation_guidance),
        )
        for item in payload.remediations
    ]
    narrative.executive_summary = sanitize_html_text(payload.executive_summary)
    narrative.business_impact = sanitize_html_text(payload.business_impact)
    narrative.remediation_priorities = [r.model_dump() for r in clean_remediations]
    narrative.approval_status = payload.approval_status

    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="AI_NARRATIVE_UPDATED",
        target_entity=f"ai_narrative:{narrative.id}",
        ip_address=get_client_ip(request),
        details={"project_id": str(project_id), "approval_status": narrative.approval_status},
    )
    db.commit()
    db.refresh(narrative)
    return _narrative_to_response(narrative)
