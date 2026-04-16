import secrets
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _generate_api_key():
    return f"pdb_{secrets.token_urlsafe(32)}"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    data_entries = relationship("DataEntry", back_populates="owner", cascade="all, delete-orphan")
    access_policies = relationship("AccessPolicy", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="owner", cascade="all, delete-orphan")


class DataEntry(Base):
    __tablename__ = "data_entries"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    owner = relationship("User", back_populates="data_entries")


class AccessPolicy(Base):
    __tablename__ = "access_policies"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    allowed_categories = Column(Text, default="*")
    allow_sensitive = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    max_requests_per_hour = Column(Integer, default=60)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    owner = relationship("User", back_populates="access_policies")
    api_keys = relationship("APIKey", back_populates="policy", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("access_policies.id"), nullable=False)
    key = Column(String(255), unique=True, index=True, nullable=False, default=_generate_api_key)
    label = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    owner = relationship("User", back_populates="api_keys")
    policy = relationship("AccessPolicy", back_populates="api_keys")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(255), nullable=False)
    detail = Column(Text, default="")
    ip_address = Column(String(45), nullable=True)
    allowed = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
