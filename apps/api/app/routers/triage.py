"""TriageRouter — PLAN.md FASE 4.5 (SDD UC-09; EC-11 optimistic locking; EC-12)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.audit import get_client_ip, record_audit_log
from app.core.crypto import decrypt_poc, get_encryption_key
from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import (
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.models.finding import Finding
from app.models.project import Project
from app.models.proof_of_concept import ProofOfConcept
from app.models.workspace_member import WorkspaceMember
from app.services.image_validator import validate_and_process_image
from app.services.s3_storage import (
    S3StorageClient,
    get_s3_bucket_name,
    make_boto_s3_client,
    make_public_boto_s3_client,
)
from vulnflow_contracts import (
    FindingListItemResponse,
    FindingListResponse,
    FindingPoCResponse,
    FindingStatus,
    FindingStatusResponse,
    FindingSummaryMetrics,
    ImageUploadRequest,
    PoCAttachmentResponse,
    Severity,
    UpdateFindingCurationRequest,
    UpdateFindingStatusRequest,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/projects/{project_id}/findings", tags=["triage"]
)

_require_triager_role = require_workspace_role({"MANAGER", "PENTESTER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})


def get_poc_upload_storage() -> S3StorageClient:
    return S3StorageClient(
        make_boto_s3_client(),
        bucket=get_s3_bucket_name(),
        public_client=make_public_boto_s3_client(),
    )


def _get_project_or_404(db: Session, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")
    return project


def _get_finding_or_404(db: Session, project_id: uuid.UUID, finding_id: uuid.UUID) -> Finding:
    finding = db.query(Finding).filter_by(id=finding_id, project_id=project_id).one_or_none()
    if finding is None:
        raise ResourceNotFoundError("Finding not found in this project.")
    return finding


@router.get("", response_model=FindingListResponse)
def list_findings(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    severity: Annotated[Severity | None, Query()] = None,
    status: Annotated[FindingStatus | None, Query()] = None,
    is_quarantined: Annotated[bool | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    _member: WorkspaceMember = Depends(_require_any_member),
    db: Session = Depends(get_db),
) -> FindingListResponse:
    _get_project_or_404(db, workspace_id, project_id)

    summary_rows = (
        db.query(
            Finding.severity,
            Finding.status,
            Finding.is_curated_for_report,
            Finding.is_quarantined,
        )
        .filter(Finding.project_id == project_id)
        .all()
    )
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    curated_count = 0
    quarantined_count = 0
    for row_sev, row_status, row_curated, row_quarantined in summary_rows:
        by_severity[row_sev] = by_severity.get(row_sev, 0) + 1
        by_status[row_status] = by_status.get(row_status, 0) + 1
        if row_curated:
            curated_count += 1
        if row_quarantined:
            quarantined_count += 1

    query = db.query(Finding).filter(Finding.project_id == project_id)
    if severity is not None:
        query = query.filter(Finding.severity == severity.value)
    if status is not None:
        query = query.filter(Finding.status == status.value)
    if is_quarantined is not None:
        query = query.filter(Finding.is_quarantined.is_(is_quarantined))
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Finding.title.ilike(pattern), Finding.target_host.ilike(pattern)))

    total = int(query.count())
    findings = query.order_by(Finding.created_at.desc()).offset(offset).limit(limit).all()

    return FindingListResponse(
        items=[
            FindingListItemResponse(
                id=str(f.id),
                project_id=str(f.project_id),
                title=f.title,
                severity=Severity(f.severity),
                cvss_score=float(f.cvss_score),
                cvss_version=f.cvss_version,
                cvss_vector=f.cvss_vector,
                cwe_id=f.cwe_id,
                target_host=f.target_host,
                target_port=f.target_port,
                endpoint_path=f.endpoint_path,
                protocol=f.protocol,
                source_tool=f.source_tool,
                status=FindingStatus(f.status),
                is_curated_for_report=f.is_curated_for_report,
                is_quarantined=f.is_quarantined,
                version=f.version,
                created_at=f.created_at,
            )
            for f in findings
        ],
        total=total,
        limit=limit,
        offset=offset,
        summary=FindingSummaryMetrics(
            total=len(summary_rows),
            curated=curated_count,
            quarantined=quarantined_count,
            by_severity=by_severity,
            by_status=by_status,
        ),
    )


@router.get("/{finding_id}/poc", response_model=FindingPoCResponse)
def get_finding_poc(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    request: Request,
    current_member: WorkspaceMember = Depends(_require_triager_role),
    db: Session = Depends(get_db),
) -> FindingPoCResponse:
    _get_project_or_404(db, workspace_id, project_id)
    finding = _get_finding_or_404(db, project_id, finding_id)
    poc = db.query(ProofOfConcept).filter_by(finding_id=finding.id).one_or_none()
    if poc is None:
        raise ResourceNotFoundError("Proof of Concept record not found for this finding.")

    raw_evidence = decrypt_poc(
        poc.encrypted_raw_evidence,
        get_encryption_key(),
        poc.iv_nonce,
        poc.auth_tag,
    ).decode("utf-8", errors="replace")

    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="POC_DECRYPTED",
        target_entity=f"finding:{finding.id}",
        ip_address=get_client_ip(request),
        details={"project_id": str(project_id), "finding_id": str(finding.id)},
    )
    db.commit()

    return FindingPoCResponse(
        finding_id=str(finding.id),
        raw_evidence=raw_evidence,
        reproduction_steps=list(poc.reproduction_steps or []),
        attachment_file_urls=list(poc.attachment_file_urls or []),
        key_version=poc.key_version,
    )


@router.patch("/{finding_id}/curation", response_model=FindingStatusResponse)
def update_finding_curation(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: UpdateFindingCurationRequest,
    request: Request,
    current_member: WorkspaceMember = Depends(_require_triager_role),
    db: Session = Depends(get_db),
) -> FindingStatusResponse:
    _get_project_or_404(db, workspace_id, project_id)
    finding = _get_finding_or_404(db, project_id, finding_id)

    if payload.unquarantine:
        if current_member.role != "MANAGER":
            raise PermissionDeniedError("Only MANAGER can unquarantine out-of-scope findings.")
        finding.is_quarantined = False

    if payload.is_curated_for_report:
        if finding.status == "FALSE_POSITIVE":
            raise ValidationFailedError(
                "FALSE_POSITIVE findings cannot be curated for reports (EC-12)."
            )
        if finding.is_quarantined:
            raise ValidationFailedError(
                "Cannot curate a quarantined finding for report without unquarantining it first."
            )

    finding.is_curated_for_report = payload.is_curated_for_report
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="FINDING_CURATION_UPDATED",
        target_entity=f"finding:{finding.id}",
        ip_address=get_client_ip(request),
        details={
            "is_curated_for_report": finding.is_curated_for_report,
            "is_quarantined": finding.is_quarantined,
            "unquarantine": payload.unquarantine,
        },
    )
    db.commit()
    return FindingStatusResponse(
        id=str(finding.id),
        status=FindingStatus(finding.status),
        version=finding.version,
        is_curated_for_report=finding.is_curated_for_report,
    )


@router.post("/{finding_id}/attachments", response_model=PoCAttachmentResponse, status_code=201)
def upload_poc_attachment(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: ImageUploadRequest,
    request: Request,
    current_member: WorkspaceMember = Depends(_require_triager_role),
    db: Session = Depends(get_db),
    storage: S3StorageClient = Depends(get_poc_upload_storage),
) -> PoCAttachmentResponse:
    _get_project_or_404(db, workspace_id, project_id)
    finding = _get_finding_or_404(db, project_id, finding_id)
    poc = db.query(ProofOfConcept).filter_by(finding_id=finding.id).one_or_none()
    if poc is None:
        raise ResourceNotFoundError("Proof of Concept record not found for this finding.")

    image_bytes, resolved_ct, ext = validate_and_process_image(
        data_base64=payload.data_base64,
        content_type=payload.content_type,
        max_bytes=5 * 1024 * 1024,
        allow_svg=False,
    )
    storage_path = (
        f"workspaces/{workspace_id}/projects/{project_id}/"
        f"findings/{finding_id}/{uuid.uuid4()}.{ext}"
    )
    storage.upload_bytes(storage_path, image_bytes, content_type=resolved_ct)
    attachment_url = storage.generate_presigned_url(storage_path, expires_in_seconds=604800)

    poc.attachment_file_urls = [*list(poc.attachment_file_urls or []), attachment_url]
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="POC_ATTACHMENT_UPLOADED",
        target_entity=f"finding:{finding.id}",
        ip_address=get_client_ip(request),
        details={"storage_path": storage_path, "content_type": resolved_ct},
    )
    db.commit()
    return PoCAttachmentResponse(attachment_url=attachment_url, storage_path=storage_path)


@router.patch("/{finding_id}/status", response_model=FindingStatusResponse)
def update_finding_status(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: UpdateFindingStatusRequest,
    request: Request,
    current_member: WorkspaceMember = Depends(_require_triager_role),
    db: Session = Depends(get_db),
) -> FindingStatusResponse:
    # F4-CRIT-01: Verify that project belongs to this workspace
    _get_project_or_404(db, workspace_id, project_id)
    finding = _get_finding_or_404(db, project_id, finding_id)

    if finding.version != payload.version:
        raise ConflictError(
            "This finding was modified by another request; reload and retry (EC-11)."
        )

    if finding.status == payload.status.value:
        return FindingStatusResponse(
            id=str(finding.id),
            status=payload.status,
            version=finding.version,
            is_curated_for_report=finding.is_curated_for_report,
        )

    old_status = finding.status
    finding.status = payload.status.value
    # `version` is NOT incremented here: `Finding.__mapper_args__` registers it
    # as SQLAlchemy's `version_id_col`, so the UPDATE carries
    # `WHERE version = :old_version` and the bump happens as part of that
    # statement. Incrementing by hand would double-count it.
    # EC-12: a finding marked FALSE_POSITIVE must never stay curated for
    # the compiled report, regardless of what the client sent.
    if payload.status.value == "FALSE_POSITIVE":
        finding.is_curated_for_report = False

    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="FINDING_STATUS_CHANGE",
        target_entity="findings",
        ip_address=get_client_ip(request),
        details={
            "finding_id": str(finding_id),
            "old_status": old_status,
            "new_status": finding.status,
        },
    )
    try:
        db.commit()
    except StaleDataError as exc:
        # The `payload.version` check above is only a fast path; it cannot stop
        # a true race, because two requests can both read version=1 before
        # either writes. This is the authoritative guard: the UPDATE matched 0
        # rows, meaning a concurrent transaction committed first (EC-11).
        db.rollback()
        raise ConflictError(
            "This finding was modified by another request; reload and retry (EC-11)."
        ) from exc

    return FindingStatusResponse(
        id=str(finding.id),
        status=payload.status,
        version=finding.version,
        is_curated_for_report=finding.is_curated_for_report,
    )
