from typing import Dict, Any, List
from src.chat_history.models import Conversation, ConversationSummary, ChatMessage


class ChatMessageMappers:
    @staticmethod
    def to_streamlit_format(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        return [{"role": msg.role, "content": msg.content, **msg.metadata} for msg in messages]

    @staticmethod
    def to_api_format(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        return [msg.to_dict() for msg in messages]


class ConversationMappers:
    @staticmethod
    def to_summary_dict(summary: ConversationSummary) -> Dict[str, Any]:
        return {
            "session_id": summary.session_id,
            "title": summary.title,
            "message_count": summary.message_count,
            "last_activity": summary.last_activity,
            "document_name": summary.document_name,
            "agent_type": summary.agent_type
        }
    
    @staticmethod
    def to_info_dict(conversation: Conversation) -> Dict[str, Any]:
        return {
            "session_id": conversation.session_id,
            "title": conversation.title,
            "message_count": conversation.message_count,
            "document_name": conversation.metadata.document_name,
            "agent_type": conversation.metadata.agent_type,
            "created_at": conversation.created_at,
            "last_activity": conversation.last_activity
        }
    
    @staticmethod
    def to_response_dict(conversation: Conversation) -> Dict[str, Any]:
        return {
            "session_id": conversation.session_id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "is_active": conversation.is_active,
            "document_name": conversation.metadata.document_name,
            "agent_type": conversation.metadata.agent_type
        }
    
    @staticmethod
    def summaries_to_list(summaries: List[ConversationSummary]) -> List[Dict[str, Any]]:
        return [ConversationMappers.to_summary_dict(s) for s in summaries]