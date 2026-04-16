from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import DataEntry, User
from app.schemas import DataEntryCreate, DataEntryOut, DataEntryUpdate

router = APIRouter(prefix="/api/data", tags=["Data Vault"])


@router.get("", response_model=list[DataEntryOut])
def list_entries(
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(DataEntry).filter(DataEntry.owner_id == user.id)
    if category:
        q = q.filter(DataEntry.category == category)
    return q.order_by(DataEntry.updated_at.desc()).all()


@router.post("", response_model=DataEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    body: DataEntryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = DataEntry(owner_id=user.id, **body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=DataEntryOut)
def get_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(DataEntry).filter(DataEntry.id == entry_id, DataEntry.owner_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router.patch("/{entry_id}", response_model=DataEntryOut)
def update_entry(
    entry_id: int,
    body: DataEntryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(DataEntry).filter(DataEntry.id == entry_id, DataEntry.owner_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(DataEntry).filter(DataEntry.id == entry_id, DataEntry.owner_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    db.delete(entry)
    db.commit()
