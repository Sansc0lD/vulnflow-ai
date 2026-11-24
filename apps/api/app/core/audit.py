"""Audit trail recording helpers — SDD §2.4.4, UC-19."""

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

SYSTEM_WORKSPACE_ID = uuid.UUID(int=0)


def get_client_ip(request: Request | None) -> str:
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first[:45]
    if request.client and request.client.host:
        return request.client.host[:45]
    return "unknown"


def record_audit_log(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_entity: str,
    ip_address: str,
    details: dict[str, Any],
) -> AuditLog:
    entry = AuditLog(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action=action[:50],
        target_entity=target_entity[:128],
        ip_address=ip_address[:45],
        details=details,
    )
    db.add(entry)
    return entry
