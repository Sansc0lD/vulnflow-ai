"""IngestRouter — PLAN.md FASE 4.4 (SDD §2.6.1.2; EC-04/EC-08/EC-09/EC-10).

This is where FASE 3's domain modules actually get wired into the system:
`ScopeEnforcer` decides `is_quarantined`, `DeduplicationService` decides
new-vs-duplicate, and `crypto` encrypts the PoC evidence before it touches
the database.
"""

import time
import uuid
from collections.abc import Callable

from fastapi import APIRouter, Depends, Header
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_poc, get_encryption_key
from app.core.dependencies import get_db, require_api_key, require_workspace_role
from app.core.exceptions import BatchLimitExceededError, ConflictError, ResourceNotFoundError
from app.core.redis_client import RedisLike, get_redis_client_factory
from app.domain.cvss import calculate_base_score
from app.domain.deduplication import compute_dedup_hash
from app.domain.scope import is_target_in_scope
from app.models.api_key import APIKey
from app.models.finding import Finding
from app.models.project import Project
from app.models.proof_of_concept import ProofOfConcept
from app.models.subscription import Subscription
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import (
    BatchIngestRequest,
    BatchIngestResponse,
    ManualFindingRequest,
    ManualFindingResponse,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/projects/{project_id}/findings", tags=["ingest"]
)

FREE_TIER_BATCH_LIMIT = 50  # EC-10
HARD_BATCH_LIMIT = 500  # SRS FR-INGEST-003
# EC-07/EDGE_CASES §5.5: long enough to cover a realistic CLI retry window
# for a large chunked upload over a bad connection, short enough that a
# genuinely new upload under the same key eventually gets a fresh outcome.
IDEMPOTENCY_TTL_SECONDS = 24 * 3600
# A placeholder written atomically (SET NX) to *claim* an Idempotency-Key
# before processing starts. Without this claim step, two requests that race
# within the GET-process-SET window both see a cache miss and both fully
# process — confirmed live by firing two concurrent requests with the same
# key: both returned 201 and both findings were persisted, silently
# bypassing the guarantee this header exists to provide. Mirrors the same
# `SET NX` pattern `DistributedLock.acquire()` already uses for EC-15.
_IDEMPOTENCY_PENDING_SENTINEL = "__pending__"
_IDEMPOTENCY_POLL_INTERVAL_SECONDS = 0.1
_IDEMPOTENCY_POLL_TIMEOUT_SECONDS = 5.0

_require_creator_role = require_workspace_role({"MANAGER", "PENTESTER"})


def _idempotency_cache_key(
    workspace_id: uuid.UUID, project_id: uuid.UUID, idempotency_key: str
) -> str:
    return f"idempotency:ingest:{workspace_id}:{project_id}:{idempotency_key}"


def _await_idempotent_result(redis_client: RedisLike, cache_key: str) -> str | None:
    """Poll briefly for the holder of `cache_key` to finish processing.

    Returns the cached response body once it's no longer the pending
    sentinel, or `None` if the holder released the claim (it failed, so
    there's no result to replay) or the poll window was exhausted.
    """
    deadline = time.monotonic() + _IDEMPOTENCY_POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        value = redis_client.get(cache_key)
        if value is None:
            return None
        if value != _IDEMPOTENCY_PENDING_SENTINEL:
            return value
        time.sleep(_IDEMPOTENCY_POLL_INTERVAL_SECONDS)
    return None


def _get_project_or_404(db: Session, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")
    return project


def _check_batch_size(db: Session, workspace_id: uuid.UUID, count: int) -> None:
    if count > HARD_BATCH_LIMIT:
        raise BatchLimitExceededError(
            f"Batch exceeds the hard limit of {HARD_BATCH_LIMIT} findings."
        )

    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    tier = subscription.tier if subscription is not None else "FREE"
    if tier == "FREE" and count > FREE_TIER_BATCH_LIMIT:
        raise BatchLimitExceededError(
            f"Free tier is limited to {FREE_TIER_BATCH_LIMIT} findings per batch."
        )


def _process_ingest_batch(
    db: Session,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: BatchIngestRequest,
) -> BatchIngestResponse:
    project = _get_project_or_404(db, workspace_id, project_id)
    _check_batch_size(db, workspace_id, len(payload.findings))

    scope_entries = project.target_scope.split("\n")
    encryption_key = get_encryption_key()
    new_count = 0
    duplicate_count = 0
    quarantined_count = 0

    for item in payload.findings:
        dedup_hash = compute_dedup_hash(
            project_id=str(project_id),
            cwe_id=item.cwe_id,
            host=item.target_host,
            port=item.target_port,
            endpoint_path=item.endpoint_path,
        )
        already_exists = (
            db.query(Finding).filter_by(project_id=project_id, dedup_hash=dedup_hash).one_or_none()
            is not None
        )
        if already_exists:
            duplicate_count += 1
            continue

        is_quarantined = not is_target_in_scope(item.target_host, scope_entries)
        if is_quarantined:
            quarantined_count += 1

        cvss_score = item.cvss_score
        if cvss_score is None and item.cvss_vector:
            cvss_score = float(calculate_base_score(item.cvss_vector))

        # F4-LOW-14: Wrap concurrent inserts in nested transaction
        # to handle duplicate dedup_hash cleanly
        try:
            with db.begin_nested():
                finding = Finding(
                    project_id=project_id,
                    dedup_hash=dedup_hash,
                    title=item.title,
                    severity=item.severity.value,
                    cvss_score=cvss_score if cvss_score is not None else 0.0,
                    cvss_version=item.cvss_version.value,
                    cvss_vector=item.cvss_vector or "",
                    cwe_id=item.cwe_id,
                    target_host=item.target_host,
                    target_port=item.target_port,
                    endpoint_path=item.endpoint_path,
                    protocol=item.protocol.value,
                    source_tool=item.source_tool.value,
                    is_quarantined=is_quarantined,
                )
                db.add(finding)
                db.flush()

                ciphertext, iv_nonce, auth_tag = encrypt_poc(
                    item.proof_of_concept.raw_evidence.encode("utf-8"), encryption_key
                )
                db.add(
                    ProofOfConcept(
                        finding_id=finding.id,
                        encrypted_raw_evidence=ciphertext,
                        iv_nonce=iv_nonce,
                        auth_tag=auth_tag,
                        reproduction_steps=item.proof_of_concept.reproduction_steps,
                        attachment_file_urls=[
                            str(url) for url in item.proof_of_concept.attachment_urls
                        ],
                    )
                )
                db.flush()
            new_count += 1
        except IntegrityError:
            duplicate_count += 1
            continue

    db.commit()
    return BatchIngestResponse(
        new_findings_count=new_count,
        duplicate_findings_count=duplicate_count,
        quarantined_count=quarantined_count,
    )


@router.post("/batch", response_model=BatchIngestResponse, status_code=201)
def ingest_batch(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: BatchIngestRequest,
    db: Session = Depends(get_db),
    _api_key: APIKey = Depends(require_api_key),
    redis_client_factory: Callable[[], RedisLike] = Depends(get_redis_client_factory),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> BatchIngestResponse:
    # EC-07: a chunk retried after a network failure carries the same
    # Idempotency-Key as its first attempt and must get back that attempt's
    # exact result, not be reprocessed — this is a per-HTTP-request gate
    # only, distinct from `dedup_hash`'s per-finding content dedup below.
    # `redis_client_factory()` is only actually called (and REDIS_URL only
    # actually required) when a caller sends this optional header.
    #
    # The key is atomically CLAIMED (SET NX) before processing, not just
    # read-then-set-after: a plain GET-then-SET-at-the-end leaves a window
    # where two requests racing on the same key both see a cache miss and
    # both fully process — confirmed live by firing two truly concurrent
    # requests with the same Idempotency-Key, both got 201 and both findings
    # were persisted. Mirrors `DistributedLock.acquire()`'s SET NX pattern.
    cache_key = None
    redis_client: RedisLike | None = None
    if idempotency_key:
        redis_client = redis_client_factory()
        cache_key = _idempotency_cache_key(workspace_id, project_id, idempotency_key)
        claimed = bool(
            redis_client.set(
                cache_key, _IDEMPOTENCY_PENDING_SENTINEL, nx=True, ex=IDEMPOTENCY_TTL_SECONDS
            )
        )
        if not claimed:
            cached_response = _await_idempotent_result(redis_client, cache_key)
            if cached_response is not None:
                return BatchIngestResponse.model_validate_json(cached_response)
            raise ConflictError(
                "A request with this Idempotency-Key is already being processed. Retry shortly."
            )

    try:
        result = _process_ingest_batch(db, workspace_id, project_id, payload)
    except Exception:
        # Release the claim on any failure (validation, scope, DB error) so
        # a genuine retry under the same key isn't stuck behind a pending
        # placeholder for the full 24h TTL — only a successful attempt's
        # real result should ever be cached.
        if redis_client is not None and cache_key is not None:
            redis_client.delete(cache_key)
        raise

    if redis_client is not None and cache_key is not None:
        redis_client.set(cache_key, result.model_dump_json(), ex=IDEMPOTENCY_TTL_SECONDS)
    return result


@router.post("/manual", response_model=ManualFindingResponse, status_code=201)
def create_manual_finding(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ManualFindingRequest,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_creator_role),
) -> ManualFindingResponse:
    project = _get_project_or_404(db, workspace_id, project_id)

    cvss_score = float(calculate_base_score(payload.cvss_vector))
    dedup_hash = compute_dedup_hash(
        project_id=str(project_id),
        cwe_id=payload.cwe_id,
        host=payload.target_host,
        port=payload.target_port,
        endpoint_path=payload.endpoint_path,
    )
    is_quarantined = not is_target_in_scope(payload.target_host, project.target_scope.split("\n"))

    finding = Finding(
        project_id=project_id,
        dedup_hash=dedup_hash,
        title=payload.title,
        severity=payload.severity.value,
        cvss_score=cvss_score,
        cvss_vector=payload.cvss_vector,
        cwe_id=payload.cwe_id,
        target_host=payload.target_host,
        target_port=payload.target_port,
        endpoint_path=payload.endpoint_path,
        protocol=payload.protocol.value,
        source_tool="manual",
        is_quarantined=is_quarantined,
    )
    db.add(finding)
    db.flush()

    ciphertext, iv_nonce, auth_tag = encrypt_poc(
        payload.proof_of_concept.raw_evidence.encode("utf-8"), get_encryption_key()
    )
    db.add(
        ProofOfConcept(
            finding_id=finding.id,
            encrypted_raw_evidence=ciphertext,
            iv_nonce=iv_nonce,
            auth_tag=auth_tag,
            reproduction_steps=payload.proof_of_concept.reproduction_steps,
            attachment_file_urls=[str(url) for url in payload.proof_of_concept.attachment_urls],
        )
    )
    db.commit()

    return ManualFindingResponse(
        id=str(finding.id),
        project_id=str(project_id),
        title=finding.title,
        severity=payload.severity,
        cvss_score=cvss_score,
        cvss_vector=finding.cvss_vector,
        cwe_id=finding.cwe_id,
        status=finding.status,  # type: ignore[arg-type]
        created_at=finding.created_at,
    )
