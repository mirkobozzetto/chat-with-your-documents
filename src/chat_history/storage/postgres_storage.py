# src/chat_history/storage/postgres_storage.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Session, select
from src.chat_history.storage.base_storage import BaseConversationStorage
from src.chat_history.models import Conversation, ConversationSummary
from src.database.models import Conversation as DbConversation
from src.database.connection import engine

class PostgresConversationStorage(BaseConversationStorage):

    def __init__(self):
        pass

    def _extract_metadata(self, conversation: Conversation) -> Dict[str, Any]:
        if hasattr(conversation.metadata, 'to_dict'):
            return conversation.metadata.to_dict()
        elif hasattr(conversation.metadata, '__dict__'):
            return conversation.metadata.__dict__
        elif isinstance(conversation.metadata, dict):
            return conversation.metadata
        else:
            return {}

    def _get_active_conversations_query(self, session: Session, additional_filters=None):
        stmt = select(DbConversation).where(DbConversation.is_active == True)
        if additional_filters:
            stmt = stmt.where(*additional_filters)
        return stmt.order_by(DbConversation.updated_at.desc())

    def _serialize_messages(self, messages: List) -> List[Dict[str, Any]]:
        return [msg.to_dict() for msg in messages]

    def _update_db_conversation_fields(self, db_conv: DbConversation, conversation: Conversation, metadata_dict: Dict[str, Any]) -> None:
        db_conv.title = conversation.title
        db_conv.messages = self._serialize_messages(conversation.messages)
        db_conv.extra_data = metadata_dict
        db_conv.document_name = metadata_dict.get('document_name')
        db_conv.agent_type = metadata_dict.get('agent_type')
        db_conv.tags = metadata_dict.get('tags', [])
        db_conv.is_active = conversation.is_active
        db_conv.updated_at = datetime.now(timezone.utc)

    def _conversations_to_summaries(self, db_conversations: List[DbConversation]) -> List[ConversationSummary]:
        return [self._create_summary(db_conv) for db_conv in db_conversations]

    def _create_summary(self, db_conv: DbConversation) -> ConversationSummary:
        return ConversationSummary(
            session_id=db_conv.id,
            title=db_conv.title or "New Conversation",
            message_count=len(db_conv.messages),
            last_activity=db_conv.updated_at,
            document_name=db_conv.document_name,
            agent_type=db_conv.agent_type,
            tags=db_conv.tags or [],
            created_at=db_conv.created_at,
            is_active=db_conv.is_active
        )

    def save_conversation(self, conversation: Conversation) -> None:
        metadata_dict = self._extract_metadata(conversation)

        with Session(engine) as session:
            existing = session.get(DbConversation, conversation.session_id)

            if existing:
                self._update_db_conversation_fields(existing, conversation, metadata_dict)
            else:
                db_conversation = DbConversation(
                    id=conversation.session_id,
                    user_id=metadata_dict.get('user_id', 'anonymous'),
                    title=conversation.title,
                    messages=self._serialize_messages(conversation.messages),
                    extra_data=metadata_dict,
                    document_name=metadata_dict.get('document_name'),
                    agent_type=metadata_dict.get('agent_type'),
                    tags=metadata_dict.get('tags', []),
                    is_active=conversation.is_active
                )
                session.add(db_conversation)

            session.commit()

    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        with Session(engine) as session:
            db_conversation = session.get(DbConversation, session_id)
            if not db_conversation or not db_conversation.is_active:
                return None

            return self._db_to_conversation(db_conversation)

    def list_conversations(self, limit: Optional[int] = None, offset: int = 0) -> List[ConversationSummary]:
        with Session(engine) as session:
            stmt = self._get_active_conversations_query(session)

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            db_conversations = session.exec(stmt).all()
            return self._conversations_to_summaries(db_conversations)

    def delete_conversation(self, session_id: str) -> bool:
        with Session(engine) as session:
            db_conversation = session.get(DbConversation, session_id)
            if not db_conversation:
                return False

            db_conversation.is_active = False
            session.commit()
            return True

    def search_conversations(self, query: str, limit: Optional[int] = None) -> List[ConversationSummary]:
        with Session(engine) as session:
            stmt = self._get_active_conversations_query(session)
            if limit:
                stmt = stmt.limit(limit)

            db_conversations = session.exec(stmt).all()

            filtered_conversations = []
            for db_conv in db_conversations:
                for msg in db_conv.messages:
                    if query.lower() in msg.get('content', '').lower():
                        filtered_conversations.append(db_conv)
                        break

            return self._conversations_to_summaries(filtered_conversations)

    def get_conversations_by_document(self, document_name: str) -> List[ConversationSummary]:
        with Session(engine) as session:
            stmt = self._get_active_conversations_query(session, [DbConversation.document_name == document_name])
            db_conversations = session.exec(stmt).all()
            return self._conversations_to_summaries(db_conversations)

    def get_conversations_by_agent(self, agent_type: str) -> List[ConversationSummary]:
        with Session(engine) as session:
            stmt = self._get_active_conversations_query(session, [DbConversation.agent_type == agent_type])
            db_conversations = session.exec(stmt).all()
            return self._conversations_to_summaries(db_conversations)

    def get_conversation_count(self) -> int:
        with Session(engine) as session:
            stmt = self._get_active_conversations_query(session)
            db_conversations = session.exec(stmt).all()
            return len(db_conversations)

    def cleanup_old_conversations(self, days_threshold: int = 30) -> int:
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

        with Session(engine) as session:
            stmt = self._get_active_conversations_query(session, [DbConversation.updated_at < cutoff_date])
            old_conversations = session.exec(stmt).all()

            for conv in old_conversations:
                conv.is_active = False

            session.commit()
            return len(old_conversations)

    def export_conversation(self, session_id: str, format: str = "json") -> Optional[Dict[str, Any]]:
        with Session(engine) as session:
            db_conversation = session.get(DbConversation, session_id)
            if not db_conversation:
                return None

            return {
                'session_id': db_conversation.id,
                'title': db_conversation.title,
                'messages': db_conversation.messages,
                'metadata': db_conversation.extra_data,
                'document_name': db_conversation.document_name,
                'agent_type': db_conversation.agent_type,
                'tags': db_conversation.tags,
                'created_at': db_conversation.created_at.isoformat(),
                'updated_at': db_conversation.updated_at.isoformat(),
                'is_active': db_conversation.is_active
            }

    def import_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        try:
            with Session(engine) as session:
                db_conversation = DbConversation(
                    id=conversation_data['session_id'],
                    user_id=conversation_data.get('user_id', 'anonymous'),
                    title=conversation_data.get('title'),
                    messages=conversation_data.get('messages', []),
                    extra_data=conversation_data.get('metadata', {}),
                    document_name=conversation_data.get('document_name'),
                    agent_type=conversation_data.get('agent_type'),
                    tags=conversation_data.get('tags', []),
                    is_active=conversation_data.get('is_active', True)
                )
                session.add(db_conversation)
                session.commit()
                return True
        except Exception:
            return False

    def _db_to_conversation(self, db_conversation: DbConversation) -> Conversation:
        from src.chat_history.models import ChatMessage, ConversationMetadata

        messages = []
        for msg_data in db_conversation.messages:
            messages.append(ChatMessage.from_dict(msg_data))

        return Conversation(
            session_id=db_conversation.id,
            title=db_conversation.title or "New Conversation",
            messages=messages,
            metadata=ConversationMetadata.from_dict({
                **db_conversation.extra_data,
                'document_name': db_conversation.document_name,
                'agent_type': db_conversation.agent_type,
                'user_id': db_conversation.user_id
            }),
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            is_active=db_conversation.is_active
        )
