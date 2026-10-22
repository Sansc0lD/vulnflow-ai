"""PLAN.md FASE 2.3 — Tabel `proofs_of_concept` (SDD §2.4.2 #8)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.core.crypto import decrypt_poc, encrypt_poc, generate_master_key
from app.models.finding import Finding
from app.models.project import Project
from app.models.proof_of_concept import ProofOfConcept
from app.models.workspace import Workspace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _make_finding(session: Session) -> Finding:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    project = Project(
        workspace_id=workspace.id,
        name="Audit",
        client_name="Klien",
        target_scope="*.klien.com",
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
    )
    session.add(project)
    session.commit()
    finding = Finding(
        project_id=project.id,
        dedup_hash="h",
        title="T",
        severity="LOW",
        cvss_score=Decimal("1.0"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        cwe_id="UNKNOWN",
        target_host="h",
        source_tool="manual",
    )
    session.add(finding)
    session.commit()
    return finding


def test_proof_of_concept_stores_encrypted_evidence_roundtrip(session: Session) -> None:
    finding = _make_finding(session)
    key = generate_master_key()
    ciphertext, iv_nonce, auth_tag = encrypt_poc(b"admin:admin on /login", key)

    poc = ProofOfConcept(
        finding_id=finding.id,
        encrypted_raw_evidence=ciphertext,
        iv_nonce=iv_nonce,
        auth_tag=auth_tag,
    )
    session.add(poc)
    session.commit()

    assert poc.key_version == 1
    recovered = decrypt_poc(poc.encrypted_raw_evidence, key, poc.iv_nonce, poc.auth_tag)
    assert recovered == b"admin:admin on /login"


def test_proof_of_concept_is_unique_per_finding(session: Session) -> None:
    finding = _make_finding(session)
    common = {"encrypted_raw_evidence": b"c", "iv_nonce": b"i" * 12, "auth_tag": b"t" * 16}

    session.add(ProofOfConcept(finding_id=finding.id, **common))
    session.commit()
    session.add(ProofOfConcept(finding_id=finding.id, **common))

    with pytest.raises(IntegrityError):
        session.commit()
