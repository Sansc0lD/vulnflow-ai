"""Audit trail recording helpers — SDD §2.4.4, UC-19."""

import ipaddress
import os
import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

SYSTEM_WORKSPACE_ID = uuid.UUID(int=0)


_TRUSTED_PRIVATE_NETS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("fc00::/7"),
)


def _is_trusted_proxy(host: str | None) -> bool:
    if not host:
        return False
    cleaned = host.strip()
    configured = {
        entry.strip()
        for entry in os.environ.get("TRUSTED_PROXY_IPS", "").split(",")
        if entry.strip()
    }
    if cleaned in configured or cleaned == "testclient":
        return True
    try:
        addr = ipaddress.ip_address(cleaned)
    except ValueError:
        return False
    return addr.is_loopback or any(addr in net for net in _TRUSTED_PRIVATE_NETS)


def get_client_ip(request: Request | None) -> str:
    if request is None:
        return "unknown"
    client_host = request.client.host if request.client and request.client.host else None
    if _is_trusted_proxy(client_host):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first = forwarded.split(",", 1)[0].strip()
            if first:
                return first[:45]
        real_ip = request.headers.get("x-real-ip")
        if real_ip and real_ip.strip():
            return real_ip.strip()[:45]
    if client_host:
        return client_host[:45]
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
