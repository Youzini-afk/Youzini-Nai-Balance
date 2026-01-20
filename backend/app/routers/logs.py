from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import RequestLog, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def list_my_logs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RequestLog)
        .where(RequestLog.user_id == user.id)
        .order_by(RequestLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "status": log.status,
            "status_code": log.status_code,
            "api_key_id": log.api_key_id,
            "width": log.width,
            "height": log.height,
            "steps": log.steps,
            "samples": log.samples,
            "latency_ms": log.latency_ms,
            "reject_reason": log.reject_reason,
            "created_at": log.created_at,
        }
        for log in logs
    ]
