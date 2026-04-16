from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Auth ----------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Data Entries ----------

class DataEntryCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100, examples=["contacts"])
    label: str = Field(..., min_length=1, max_length=255, examples=["Work email"])
    content: str = Field(..., min_length=1, examples=["alice@example.com"])
    is_sensitive: bool = False


class DataEntryUpdate(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    label: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    is_sensitive: Optional[bool] = None


class DataEntryOut(BaseModel):
    id: int
    category: str
    label: str
    content: str
    is_sensitive: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Access Policies ----------

class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["ChatGPT – Read contacts"])
    description: str = ""
    allowed_categories: str = Field(
        default="*",
        examples=["contacts,calendar"],
        description="Comma-separated category names, or '*' for all",
    )
    allow_sensitive: bool = False
    max_requests_per_hour: int = Field(default=60, ge=1, le=10000)


class PolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    allowed_categories: Optional[str] = None
    allow_sensitive: Optional[bool] = None
    is_active: Optional[bool] = None
    max_requests_per_hour: Optional[int] = Field(None, ge=1, le=10000)


class PolicyOut(BaseModel):
    id: int
    name: str
    description: str
    allowed_categories: str
    allow_sensitive: bool
    is_active: bool
    max_requests_per_hour: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- API Keys ----------

class APIKeyCreate(BaseModel):
    policy_id: int
    label: str = Field(..., min_length=1, max_length=255, examples=["My ChatGPT Plugin"])


class APIKeyOut(BaseModel):
    id: int
    policy_id: int
    key: str
    label: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyBrief(BaseModel):
    id: int
    policy_id: int
    key_prefix: str
    label: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Audit Logs ----------

class AuditLogOut(BaseModel):
    id: int
    api_key_id: Optional[int]
    action: str
    resource: str
    detail: str
    ip_address: Optional[str]
    allowed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Broker Request / Response ----------

class BrokerQuery(BaseModel):
    categories: Optional[list[str]] = Field(
        None,
        description="Filter by categories. Omit to request all allowed categories.",
    )
    search: Optional[str] = Field(None, description="Full-text search across labels and content")
    include_sensitive: bool = False


class BrokerDataItem(BaseModel):
    category: str
    label: str
    content: str


class BrokerResponse(BaseModel):
    allowed: bool
    data: list[BrokerDataItem]
    filtered_count: int = Field(description="How many entries matched the query")
    policy_name: str
