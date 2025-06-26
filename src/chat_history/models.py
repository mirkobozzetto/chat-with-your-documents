# src/chat_history/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationMetadata:
    document_name: Optional[str] = None
    agent_type: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    user_info: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_name": self.document_name,
            "agent_type": self.agent_type,
            "agent_config": self.agent_config,
            "user_info": self.user_info,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMetadata':
        return cls(
            document_name=data.get("document_name"),
            agent_type=data.get("agent_type"),
            agent_config=data.get("agent_config"),
            user_info=data.get("user_info"),
            tags=data.get("tags", [])
        )


@dataclass
class Conversation:
    session_id: str
    title: str
    messages: List[ChatMessage]
    metadata: ConversationMetadata
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def last_activity(self) -> datetime:
        if self.messages:
            return max(msg.timestamp for msg in self.messages)
        return self.updated_at

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()

        if self.title == "New Conversation" and len(self.messages) >= 2:
            self._auto_generate_title()

    def _auto_generate_title(self) -> None:
        first_user_message = next((msg.content for msg in self.messages if msg.role == "user"), "")
        if first_user_message:
            self.title = first_user_message[:50] + ("..." if len(first_user_message) > 50 else "")

    def update_metadata(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        return cls(
            session_id=data["session_id"],
            title=data["title"],
            messages=[ChatMessage.from_dict(msg) for msg in data["messages"]],
            metadata=ConversationMetadata.from_dict(data["metadata"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_active=data.get("is_active", True)
        )

    @classmethod
    def create_new(cls, title: str = "New Conversation", **metadata_kwargs) -> 'Conversation':
        now = datetime.now()
        return cls(
            session_id=str(uuid.uuid4()),
            title=title,
            messages=[],
            metadata=ConversationMetadata(**metadata_kwargs),
            created_at=now,
            updated_at=now
        )


@dataclass
class ConversationSummary:
    session_id: str
    title: str
    message_count: int
    last_activity: datetime
    document_name: Optional[str]
    agent_type: Optional[str]
    tags: List[str]
    created_at: Optional[datetime] = None
    is_active: bool = True


    @classmethod
    def from_conversation(cls, conversation: Conversation) -> 'ConversationSummary':
        return cls(
            session_id=conversation.session_id,
            title=conversation.title,
            message_count=conversation.message_count,
            last_activity=conversation.last_activity,
            document_name=conversation.metadata.document_name,
            agent_type=conversation.metadata.agent_type,
            tags=conversation.metadata.tags
        )
