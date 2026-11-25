"""AIRouter — PLAN.md FASE 4.6 (SDD §2.6.1.3, UC-11; EC-13/EC-14) + Issue #9 async & rate limit."""

import json
import os
import time
import uuid
from collections.abc import Generator
from typing import Any, Literal, Protocol

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.audit import get_client_ip, record_audit_log
from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.core.redis_client import get_optional_redis_client
from app.domain.ai_ghostwriter import LLMAdapter
from app.domain.sanitizer import sanitize_html_text
from app.models.ai_narrative import AINarrative
from app.models.finding import Finding
from app.models.project import Project
from app.models.subscription import Subscription
from app.models.workspace_member import WorkspaceMember
from app.services.gemini_adapter import (
    DEFAULT_GEMINI_FALLBACK_MODEL,
    DEFAULT_GEMINI_MODEL,
    GeminiLLMAdapter,
)
from app.workers.ai_worker import run_ai_narrative_generation
from vulnflow_contracts import (
    AIJobStatus,
    AINarrativeAcceptedResponse,
    AINarrativeJobStatusResponse,
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
_AI_JOB_STATUS_TTL_SECONDS = 3600
_RPM_LIMIT_PER_WORKSPACE = int(os.environ.get("AI_WORKSPACE_RPM_LIMIT", "3"))
_DAILY_AI_LIMIT_BY_TIER = {"FREE": 5, "PRO": 50, "ENTERPRISE": 500}


class AINarrativeEnqueuer(Protocol):
    def __call__(self, **kwargs: Any) -> str: ...


def get_ai_enqueuer() -> AINarrativeEnqueuer:
    from app.workers.ai_worker import generate_narrative_task

    def _enqueue(**kwargs: Any) -> str:
        result: Any = generate_narrative_task.delay(**kwargs)
        return str(result.id)

    return _enqueue


def get_llm_adapter() -> Generator[LLMAdapter, None, None]:
    """Default (production) adapter. Routers depend on this indirection so
    tests can override it with a fake — never hitting the real Gemini API."""
    with httpx.Client(timeout=45.0) as client:
        provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
        if provider == "ollama":
            from app.services.ollama_adapter import OllamaLLMAdapter

            yield OllamaLLMAdapter(
                base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                model=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
                client=client,
            )
            return
        yield GeminiLLMAdapter(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            fallback_model=os.environ.get("GEMINI_FALLBACK_MODEL", DEFAULT_GEMINI_FALLBACK_MODEL),
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


def _enforce_workspace_ai_rate_limit(
    redis_client: Any | None, *, workspace_id: uuid.UUID, db: Session
) -> None:
    if redis_client is None or not hasattr(redis_client, "incr"):
        return

    minute_bucket = int(time.time() // 60)
    rpm_key = f"ratelimit:ai:rpm:{workspace_id}:{minute_bucket}"
    day_bucket = int(time.time() // 86400)
    day_key = f"ratelimit:ai:daily:{workspace_id}:{day_bucket}"

    sub = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    tier = sub.tier if sub is not None else "FREE"
    daily_limit = _DAILY_AI_LIMIT_BY_TIER.get(tier, 5)

    try:
        rpm_count = int(redis_client.incr(rpm_key))
        if rpm_count == 1 and hasattr(redis_client, "expire"):
            redis_client.expire(rpm_key, 120)
        if rpm_count > _RPM_LIMIT_PER_WORKSPACE:
            raise HTTPException(
                status_code=429,
                detail="AI generation rate limit exceeded for this workspace. Retry shortly.",
                headers={"Retry-After": "60"},
            )

        daily_count = int(redis_client.incr(day_key))
        if daily_count == 1 and hasattr(redis_client, "expire"):
            redis_client.expire(day_key, 90000)
        if daily_count > daily_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Daily AI quota ({daily_limit}/day) reached for {tier} tier.",
                headers={"Retry-After": "3600"},
            )
    except (RedisError, OSError, TypeError, ValueError):
        return


def _validate_project_and_findings(
    db: Session, *, workspace_id: uuid.UUID, project_id: uuid.UUID, finding_ids: list[str]
) -> tuple[Project, list[Finding]]:
    # F4-CRIT-02: Validate that project belongs to this workspace
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    # F4-MED-16: Catch invalid UUID format from client input
    try:
        parsed_ids = [uuid.UUID(fid) for fid in finding_ids]
    except ValueError as exc:
        raise ValidationFailedError(f"Invalid UUID in finding_ids: {exc}") from exc

    unique_ids = list(dict.fromkeys(parsed_ids))
    findings = (
        db.query(Finding).filter(Finding.project_id == project_id, Finding.id.in_(unique_ids)).all()
    )
    if len(findings) != len(unique_ids):
        raise ResourceNotFoundError("One or more findings were not found in this project.")

    if any(f.is_quarantined or f.status == "FALSE_POSITIVE" for f in findings):
        raise ValidationFailedError(
            "Quarantined or FALSE_POSITIVE findings cannot be included in AI narratives."
        )
    return project, findings


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
    project, findings = _validate_project_and_findings(
        db, workspace_id=workspace_id, project_id=project_id, finding_ids=payload.finding_ids
    )
    _enforce_workspace_ai_rate_limit(redis_client, workspace_id=workspace_id, db=db)

    narrative = run_ai_narrative_generation(
        db,
        workspace_id=workspace_id,
        project=project,
        findings=findings,
        tone=payload.tone,
        language=payload.language,
        llm_adapter=llm_adapter,
        redis_client=redis_client,
        actor_user_id=current_member.user_id,
        ip_address=get_client_ip(request),
    )
    return _narrative_to_response(narrative)


@router.post("/ai-narratives/async", response_model=AINarrativeAcceptedResponse, status_code=202)
def enqueue_narrative_generation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: AINarrativeRequest,
    db: Session = Depends(get_db),
    redis_client: Any | None = Depends(get_optional_redis_client),
    enqueue: AINarrativeEnqueuer = Depends(get_ai_enqueuer),
    current_member: WorkspaceMember = Depends(_require_requester_role),
) -> AINarrativeAcceptedResponse:
    _project, findings = _validate_project_and_findings(
        db, workspace_id=workspace_id, project_id=project_id, finding_ids=payload.finding_ids
    )
    _enforce_workspace_ai_rate_limit(redis_client, workspace_id=workspace_id, db=db)

    job_id = enqueue(
        workspace_id=str(workspace_id),
        project_id=str(project_id),
        finding_ids=[str(f.id) for f in findings],
        tone=payload.tone,
        language=payload.language,
        actor_user_id=str(current_member.user_id),
    )
    if redis_client is not None:
        initial_job = {
            "job_id": job_id,
            "workspace_id": str(workspace_id),
            "status": AIJobStatus.QUEUED.value,
            "progress_percentage": 10,
            "stage": "Queued for AI draft generation",
            "narrative_id": None,
            "error_message": None,
        }
        initial_json = json.dumps(initial_job)
        with __import__("contextlib").suppress(RedisError, OSError):
            try:
                redis_client.set(
                    f"job:ai:{job_id}",
                    initial_json,
                    ex=_AI_JOB_STATUS_TTL_SECONDS,
                    nx=True,
                )
            except TypeError:
                if redis_client.get(f"job:ai:{job_id}") is None:
                    redis_client.set(
                        f"job:ai:{job_id}", initial_json, ex=_AI_JOB_STATUS_TTL_SECONDS
                    )

    return AINarrativeAcceptedResponse(
        job_id=job_id,
        message="AI narrative generation has been queued.",
        status_url=(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/reports/ai-narratives/jobs/{job_id}"
        ),
    )


@router.get("/ai-narratives/jobs/{job_id}", response_model=AINarrativeJobStatusResponse)
def get_narrative_job_status(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: str,
    db: Session = Depends(get_db),
    redis_client: Any | None = Depends(get_optional_redis_client),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> AINarrativeJobStatusResponse:
    if redis_client is None:
        raise ResourceNotFoundError("AI generation job not found.")
    raw = redis_client.get(f"job:ai:{job_id}")
    if not raw:
        raise ResourceNotFoundError("AI generation job not found.")
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ResourceNotFoundError("AI generation job not found.") from exc
    if data.get("workspace_id") != str(workspace_id):
        raise ResourceNotFoundError("AI generation job not found.")

    status = AIJobStatus(str(data.get("status", AIJobStatus.QUEUED.value)))
    narrative_id = data.get("narrative_id")
    hydrated: AINarrativeResponse | None = None
    if status == AIJobStatus.COMPLETED and narrative_id:
        with __import__("contextlib").suppress(ValueError):
            row = (
                db.query(AINarrative)
                .filter_by(id=uuid.UUID(str(narrative_id)), project_id=project_id)
                .one_or_none()
            )
            if row is not None:
                hydrated = _narrative_to_response(row)

    return AINarrativeJobStatusResponse(
        job_id=job_id,
        status=status,
        progress_percentage=data.get("progress_percentage"),
        stage=data.get("stage"),
        narrative_id=str(narrative_id) if narrative_id else None,
        narrative=hydrated,
        error_message=data.get("error_message"),
    )


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
