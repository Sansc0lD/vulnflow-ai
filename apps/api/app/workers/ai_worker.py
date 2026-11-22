"""AI Ghostwriter Celery Worker & Orchestration — Issue #9 (async queue + cache)."""

import contextlib
import hashlib
import json
import os
import uuid
from typing import Any

import httpx
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.audit import record_audit_log
from app.core.redis_client import get_optional_redis_client, get_redis_client
from app.domain.ai_ghostwriter import (
    LLMAdapter,
    _build_fallback_narrative,
    generate_ai_narrative_detailed,
)
from app.domain.sanitizer import sanitize_text, whitelist_finding_metadata, whitelist_tech_stack
from app.domain.telemetry import compute_ai_telemetry, get_monthly_spend_ceiling_usd
from app.models.ai_narrative import AINarrative
from app.models.finding import Finding
from app.models.project import Project
from app.services.gemini_adapter import (
    DEFAULT_GEMINI_FALLBACK_MODEL,
    DEFAULT_GEMINI_MODEL,
    GeminiLLMAdapter,
)
from app.workers.celery_app import celery_app
from vulnflow_contracts import NarrativeContent

_AI_JOB_STATUS_TTL_SECONDS = 3600
_PROMPT_CACHE_TTL_SECONDS = 6 * 3600


def build_narrative_cache_key(
    *,
    findings: list[Finding],
    tone: str,
    language: str,
    tech_stack: dict[str, str] | None = None,
) -> str:
    canonical_findings = sorted(
        [
            whitelist_finding_metadata(
                {
                    "title": sanitize_text(f.title),
                    "cwe_id": f.cwe_id,
                    "cvss_score": float(f.cvss_score),
                    "severity": f.severity,
                }
            )
            for f in findings
        ],
        key=lambda item: (str(item.get("cwe_id")), str(item.get("title"))),
    )
    payload = {
        "tone": tone,
        "language": language,
        "tech_stack": tech_stack or {},
        "findings": canonical_findings,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"cache:ai:narrative:{digest}"


def _read_cached_narrative(redis_client: Any | None, cache_key: str) -> NarrativeContent | None:
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(cache_key)
    except (RedisError, OSError, AttributeError):
        return None
    if not raw:
        return None
    with contextlib.suppress(Exception):
        return NarrativeContent.model_validate_json(raw)
    return None


def _write_cached_narrative(
    redis_client: Any | None, cache_key: str, content: NarrativeContent
) -> None:
    if redis_client is None:
        return
    with contextlib.suppress(Exception):
        redis_client.set(cache_key, content.model_dump_json(), ex=_PROMPT_CACHE_TTL_SECONDS)


def run_ai_narrative_generation(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    project: Project,
    findings: list[Finding],
    tone: str,
    language: str,
    llm_adapter: LLMAdapter,
    redis_client: Any | None,
    actor_user_id: uuid.UUID | None,
    ip_address: str,
) -> AINarrative:
    """Shared generation pipeline for sync route and async Celery worker."""
    raw_stack = getattr(project, "tech_stack", None)
    safe_stack = whitelist_tech_stack(raw_stack if isinstance(raw_stack, dict) else None)

    try:
        ceiling = get_monthly_spend_ceiling_usd(redis_client)
    except (RedisError, OSError):
        ceiling = get_monthly_spend_ceiling_usd(None)
    telemetry = compute_ai_telemetry(db, spend_ceiling_usd=ceiling)

    cache_key = build_narrative_cache_key(
        findings=findings, tone=tone, language=language, tech_stack=safe_stack
    )
    cached_content = _read_cached_narrative(redis_client, cache_key)

    tokens_consumed = 0
    prompt_tokens = 0
    candidates_tokens = 0
    model_used: str | None = None
    is_fallback = False

    if cached_content is not None:
        content = cached_content
        model_used = "prompt_cache"
    elif telemetry.circuit_breaker_active:
        content = _build_fallback_narrative(findings, tech_stack=safe_stack or None)
        model_used = "circuit_breaker_fallback"
        is_fallback = True
    else:
        detailed = generate_ai_narrative_detailed(
            findings,
            tone=tone,
            language=language,
            llm_adapter=llm_adapter,
            tech_stack=safe_stack or None,
        )
        content = detailed.content
        tokens_consumed = detailed.tokens_consumed
        prompt_tokens = detailed.prompt_tokens
        candidates_tokens = detailed.candidates_tokens
        model_used = detailed.model_used
        is_fallback = detailed.is_fallback
        if not is_fallback:
            _write_cached_narrative(redis_client, cache_key, content)

    narrative = AINarrative(
        project_id=project.id,
        executive_summary=content.executive_summary,
        business_impact=content.business_impact,
        remediation_priorities=[r.model_dump() for r in content.remediations],
        tokens_consumed=tokens_consumed,
        prompt_tokens=prompt_tokens,
        candidates_tokens=candidates_tokens,
        model_used=model_used,
        is_fallback=is_fallback,
    )
    db.add(narrative)
    db.flush()
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action="AI_NARRATIVE_GENERATED",
        target_entity=f"ai_narrative:{narrative.id}",
        ip_address=ip_address,
        details={
            "project_id": str(project.id),
            "tokens_consumed": tokens_consumed,
            "prompt_tokens": prompt_tokens,
            "candidates_tokens": candidates_tokens,
            "model_used": model_used,
            "is_fallback": is_fallback,
            "cache_hit": cached_content is not None,
            "findings_count": len(findings),
        },
    )
    db.commit()
    db.refresh(narrative)
    return narrative


def _update_ai_job_status(
    job_id: str | None,
    *,
    workspace_id: str,
    status: str,
    progress_percentage: int,
    stage: str | None = None,
    narrative_id: str | None = None,
    error_message: str | None = None,
) -> None:
    if not job_id:
        return
    with contextlib.suppress(Exception):
        redis_client = get_redis_client()
        payload = {
            "job_id": job_id,
            "workspace_id": workspace_id,
            "status": status,
            "progress_percentage": progress_percentage,
            "stage": stage,
            "narrative_id": narrative_id,
            "error_message": error_message,
        }
        redis_client.set(
            f"job:ai:{job_id}",
            json.dumps(payload),
            ex=_AI_JOB_STATUS_TTL_SECONDS,
        )


def _make_worker_llm_adapter(client: httpx.Client) -> LLMAdapter:
    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    if provider == "ollama":
        from app.services.ollama_adapter import OllamaLLMAdapter

        return OllamaLLMAdapter(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
            client=client,
        )
    return GeminiLLMAdapter(
        api_key=os.environ.get("GEMINI_API_KEY", ""),
        model=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        fallback_model=os.environ.get("GEMINI_FALLBACK_MODEL", DEFAULT_GEMINI_FALLBACK_MODEL),
        client=client,
    )


@celery_app.task(bind=True)  # type: ignore[untyped-decorator] # celery ships no stubs
def generate_narrative_task(
    self: Any,
    *,
    workspace_id: str,
    project_id: str,
    finding_ids: list[str],
    tone: str,
    language: str,
    actor_user_id: str | None = None,
) -> str:
    from app.core.dependencies import get_db

    task_id = str(getattr(self.request, "id", "") or "")
    _update_ai_job_status(
        task_id,
        workspace_id=workspace_id,
        status="PROCESSING",
        progress_percentage=30,
        stage="Analyzing sanitized findings",
    )

    db_gen = get_db()
    db = next(db_gen)
    try:
        ws_uuid = uuid.UUID(workspace_id)
        proj_uuid = uuid.UUID(project_id)
        parsed_ids = [uuid.UUID(fid) for fid in finding_ids]

        project = db.query(Project).filter_by(id=proj_uuid, workspace_id=ws_uuid).one_or_none()
        if project is None:
            raise ValueError("Project not found in workspace.")
        findings = (
            db.query(Finding)
            .filter(
                Finding.project_id == proj_uuid,
                Finding.id.in_(parsed_ids),
                Finding.is_quarantined.is_(False),
                Finding.status != "FALSE_POSITIVE",
            )
            .all()
        )
        if not findings:
            raise ValueError("No eligible findings available for AI generation.")

        _update_ai_job_status(
            task_id,
            workspace_id=workspace_id,
            status="PROCESSING",
            progress_percentage=65,
            stage="Drafting executive summary & remediation guidance",
        )
        redis_client = get_optional_redis_client()
        with httpx.Client(timeout=45.0) as client:
            adapter = _make_worker_llm_adapter(client)
            narrative = run_ai_narrative_generation(
                db,
                workspace_id=ws_uuid,
                project=project,
                findings=findings,
                tone=tone,
                language=language,
                llm_adapter=adapter,
                redis_client=redis_client,
                actor_user_id=uuid.UUID(actor_user_id) if actor_user_id else None,
                ip_address="worker",
            )

        _update_ai_job_status(
            task_id,
            workspace_id=workspace_id,
            status="COMPLETED",
            progress_percentage=100,
            stage="Narrative draft ready",
            narrative_id=str(narrative.id),
        )
        return str(narrative.id)
    except Exception as exc:
        _update_ai_job_status(
            task_id,
            workspace_id=workspace_id,
            status="FAILED",
            progress_percentage=0,
            stage="Generation failed",
            error_message=str(exc),
        )
        raise
    finally:
        with contextlib.suppress(StopIteration):
            next(db_gen)
