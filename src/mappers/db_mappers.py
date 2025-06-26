from typing import Dict, Any
from src.database.models import Conversation as DbConversation


class DbConversationMappers:
    @staticmethod
    def to_export_dict(db_conv: DbConversation) -> Dict[str, Any]:
        return {
            'session_id': db_conv.id,
            'title': db_conv.title,
            'messages': db_conv.messages,
            'metadata': db_conv.extra_data,
            'document_name': db_conv.document_name,
            'agent_type': db_conv.agent_type,
            'tags': db_conv.tags,
            'created_at': db_conv.created_at.isoformat(),
            'updated_at': db_conv.updated_at.isoformat(),
            'is_active': db_conv.is_active
        }