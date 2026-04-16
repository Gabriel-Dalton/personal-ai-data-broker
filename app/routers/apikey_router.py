from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import APIKey, AccessPolicy, User
from app.schemas import APIKeyBrief, APIKeyCreate, APIKeyOut

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


@router.get("", response_model=list[APIKeyBrief])
def list_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    keys = db.query(APIKey).filter(APIKey.owner_id == user.id).order_by(APIKey.created_at.desc()).all()
    return [
        APIKeyBrief(
            id=k.id,
            policy_id=k.policy_id,
            key_prefix=k.key[:12] + "...",
            label=k.label,
            is_active=k.is_active,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post("", response_model=APIKeyOut, status_code=status.HTTP_201_CREATED)
def create_key(
    body: APIKeyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(AccessPolicy)
        .filter(AccessPolicy.id == body.policy_id, AccessPolicy.owner_id == user.id)
        .first()
    )
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    key = APIKey(owner_id=user.id, policy_id=body.policy_id, label=body.label)
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.owner_id == user.id).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    key.is_active = False
    db.commit()


@router.post("/{key_id}/toggle", response_model=APIKeyBrief)
def toggle_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.owner_id == user.id).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    key.is_active = not key.is_active
    db.commit()
    db.refresh(key)
    return APIKeyBrief(
        id=key.id,
        policy_id=key.policy_id,
        key_prefix=key.key[:12] + "...",
        label=key.label,
        is_active=key.is_active,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
    )
