from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import APIKey, AuditLog, User
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_key_ids = [k.id for k in db.query(APIKey).filter(APIKey.owner_id == user.id).all()]
    if not user_key_ids:
        return []
    return (
        db.query(AuditLog)
        .filter(AuditLog.api_key_id.in_(user_key_ids))
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
