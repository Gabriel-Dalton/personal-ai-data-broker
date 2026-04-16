from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AccessPolicy, User
from app.schemas import PolicyCreate, PolicyOut, PolicyUpdate

router = APIRouter(prefix="/api/policies", tags=["Access Policies"])


@router.get("", response_model=list[PolicyOut])
def list_policies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(AccessPolicy)
        .filter(AccessPolicy.owner_id == user.id)
        .order_by(AccessPolicy.created_at.desc())
        .all()
    )


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(
    body: PolicyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = AccessPolicy(owner_id=user.id, **body.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(AccessPolicy)
        .filter(AccessPolicy.id == policy_id, AccessPolicy.owner_id == user.id)
        .first()
    )
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicyOut)
def update_policy(
    policy_id: int,
    body: PolicyUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(AccessPolicy)
        .filter(AccessPolicy.id == policy_id, AccessPolicy.owner_id == user.id)
        .first()
    )
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(AccessPolicy)
        .filter(AccessPolicy.id == policy_id, AccessPolicy.owner_id == user.id)
        .first()
    )
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    db.delete(policy)
    db.commit()
