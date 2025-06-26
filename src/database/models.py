# src/database/models.py
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    __table_args__ = {'extend_existing': True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    extra_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    document_name: Optional[str] = None
    agent_type: Optional[str] = None
    tags: List[str] = Field(default=[], sa_column=Column(JSONB))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
