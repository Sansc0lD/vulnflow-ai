"""AI token telemetry & spend ceiling calculations — FR-ADM-001 / UC-17."""

import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_narrative import AINarrative
from app.models.project import Project
from app.models.workspace import Workspace
from vulnflow_contracts import AITelemetryResponse, WorkspaceTokenUsage

TOKEN_COST_USD_PER_MILLION = 0.15
INPUT_TOKEN_COST_USD_PER_MILLION = 0.15
OUTPUT_TOKEN_COST_USD_PER_MILLION = 0.60
USD_TO_IDR_RATE = 16_000
DEFAULT_MONTHLY_SPEND_CEILING_USD = 100.0
_SPEND_CEILING_REDIS_KEY = "admin:ai:spend_ceiling_usd"


def get_monthly_spend_ceiling_usd(redis_client: Any | None = None) -> float:
    if redis_client is not None:
        raw = redis_client.get(_SPEND_CEILING_REDIS_KEY)
        if raw is not None:
            try:
                val = float(raw)
                if val > 0:
                    return val
            except ValueError:
                pass
    env_raw = os.environ.get("AI_MONTHLY_SPEND_CEILING_USD", "")
    if env_raw:
        try:
            val = float(env_raw)
            if val > 0:
                return val
        except ValueError:
            pass
    return DEFAULT_MONTHLY_SPEND_CEILING_USD


def set_monthly_spend_ceiling_usd(redis_client: Any, ceiling_usd: float) -> None:
    redis_client.set(_SPEND_CEILING_REDIS_KEY, f"{ceiling_usd:.4f}")


def estimate_cost_usd(total_tokens: int) -> float:
    return round((total_tokens / 1_000_000) * TOKEN_COST_USD_PER_MILLION, 6)


def estimate_cost_usd_breakdown(
    *, prompt_tokens: int, candidates_tokens: int, total_tokens: int
) -> float:
    if prompt_tokens > 0 or candidates_tokens > 0:
        input_cost = (prompt_tokens / 1_000_000) * INPUT_TOKEN_COST_USD_PER_MILLION
        output_cost = (candidates_tokens / 1_000_000) * OUTPUT_TOKEN_COST_USD_PER_MILLION
        return round(input_cost + output_cost, 6)
    return estimate_cost_usd(total_tokens)


def estimate_cost_idr(cost_usd: float) -> int:
    return round(cost_usd * USD_TO_IDR_RATE)


def compute_ai_telemetry(db: Session, *, spend_ceiling_usd: float) -> AITelemetryResponse:
    now = datetime.now(UTC)
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)

    rows = (
        db.query(
            Workspace.id,
            Workspace.name,
            func.coalesce(func.sum(AINarrative.tokens_consumed), 0),
            func.coalesce(func.sum(AINarrative.prompt_tokens), 0),
            func.coalesce(func.sum(AINarrative.candidates_tokens), 0),
            func.count(AINarrative.id),
        )
        .join(Project, Project.workspace_id == Workspace.id)
        .join(AINarrative, AINarrative.project_id == Project.id)
        .filter(AINarrative.generated_at >= month_start)
        .group_by(Workspace.id, Workspace.name)
        .all()
    )

    fallback_counts_rows = (
        db.query(Workspace.id, func.count(AINarrative.id))
        .join(Project, Project.workspace_id == Workspace.id)
        .join(AINarrative, AINarrative.project_id == Project.id)
        .filter(AINarrative.generated_at >= month_start, AINarrative.is_fallback.is_(True))
        .group_by(Workspace.id)
        .all()
    )
    fallback_by_ws = {ws_id: int(cnt) for ws_id, cnt in fallback_counts_rows}

    total_tokens = 0
    total_cost_usd = 0.0
    total_narratives = 0
    total_fallbacks = 0
    by_workspace: list[WorkspaceTokenUsage] = []

    for ws_id, ws_name, ws_tokens_raw, ws_prompt_raw, ws_cand_raw, ws_count_raw in rows:
        ws_tokens = int(ws_tokens_raw or 0)
        ws_prompt = int(ws_prompt_raw or 0)
        ws_cand = int(ws_cand_raw or 0)
        ws_count = int(ws_count_raw or 0)
        ws_fb = fallback_by_ws.get(ws_id, 0)
        ws_cost_usd = estimate_cost_usd_breakdown(
            prompt_tokens=ws_prompt, candidates_tokens=ws_cand, total_tokens=ws_tokens
        )
        total_tokens += ws_tokens
        total_cost_usd = round(total_cost_usd + ws_cost_usd, 6)
        total_narratives += ws_count
        total_fallbacks += ws_fb
        by_workspace.append(
            WorkspaceTokenUsage(
                workspace_id=str(ws_id),
                workspace_name=ws_name,
                total_tokens=ws_tokens,
                narrative_count=ws_count,
                fallback_count=ws_fb,
                estimated_cost_usd=ws_cost_usd,
                estimated_cost_idr=estimate_cost_idr(ws_cost_usd),
            )
        )

    fallback_ratio = round(total_fallbacks / total_narratives, 4) if total_narratives > 0 else 0.0
    return AITelemetryResponse(
        total_tokens=total_tokens,
        total_narratives=total_narratives,
        fallback_count=total_fallbacks,
        fallback_ratio=fallback_ratio,
        estimated_cost_usd=total_cost_usd,
        estimated_cost_idr=estimate_cost_idr(total_cost_usd),
        monthly_spend_ceiling_usd=spend_ceiling_usd,
        circuit_breaker_active=total_cost_usd >= spend_ceiling_usd,
        by_workspace=by_workspace,
    )
