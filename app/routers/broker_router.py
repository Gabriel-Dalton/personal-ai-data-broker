from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import APIKey, AuditLog, DataEntry
from app.schemas import BrokerDataItem, BrokerQuery, BrokerResponse

router = APIRouter(prefix="/broker", tags=["Broker (AI-facing)"])


def _log(db: Session, *, api_key_id: int | None, action: str, resource: str, detail: str, ip: str | None, allowed: bool):
    entry = AuditLog(
        api_key_id=api_key_id,
        action=action,
        resource=resource,
        detail=detail,
        ip_address=ip,
        allowed=allowed,
    )
    db.add(entry)
    db.commit()


def _resolve_api_key(db: Session, authorization: str | None) -> APIKey:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    raw = authorization.removeprefix("Bearer ").strip()
    key = db.query(APIKey).filter(APIKey.key == raw).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not key.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key is revoked")
    if not key.policy.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Policy is disabled")
    return key


@router.post("/query", response_model=BrokerResponse)
def broker_query(
    body: BrokerQuery,
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None

    try:
        api_key = _resolve_api_key(db, authorization)
    except HTTPException as exc:
        _log(db, api_key_id=None, action="broker_query", resource="broker", detail=exc.detail, ip=ip, allowed=False)
        raise

    policy = api_key.policy
    allowed_cats = None if policy.allowed_categories.strip() == "*" else {
        c.strip().lower() for c in policy.allowed_categories.split(",") if c.strip()
    }

    q = db.query(DataEntry).filter(DataEntry.owner_id == api_key.owner_id)

    if body.categories:
        requested = {c.lower() for c in body.categories}
        if allowed_cats is not None:
            denied = requested - allowed_cats
            if denied:
                _log(
                    db, api_key_id=api_key.id, action="broker_query", resource="broker",
                    detail=f"Denied categories: {denied}", ip=ip, allowed=False,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Policy does not allow categories: {', '.join(sorted(denied))}",
                )
        q = q.filter(DataEntry.category.in_(body.categories))
    elif allowed_cats is not None:
        q = q.filter(DataEntry.category.in_(allowed_cats))

    if not body.include_sensitive or not policy.allow_sensitive:
        q = q.filter(DataEntry.is_sensitive == False)  # noqa: E712

    if body.search:
        pattern = f"%{body.search}%"
        q = q.filter(
            DataEntry.label.ilike(pattern) | DataEntry.content.ilike(pattern)
        )

    entries = q.order_by(DataEntry.category, DataEntry.label).all()

    api_key.last_used_at = datetime.now(timezone.utc)
    _log(
        db, api_key_id=api_key.id, action="broker_query", resource="broker",
        detail=f"Returned {len(entries)} entries", ip=ip, allowed=True,
    )

    return BrokerResponse(
        allowed=True,
        data=[BrokerDataItem(category=e.category, label=e.label, content=e.content) for e in entries],
        filtered_count=len(entries),
        policy_name=policy.name,
    )
