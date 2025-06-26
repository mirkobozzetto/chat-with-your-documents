from typing import Dict, Any, List
from src.chat_history.models import Conversation, ConversationSummary
from .conversation_mappers import ConversationMappers


class APIResponseMappers:
    @staticmethod
    def conversation_to_response(conversation: Conversation, messages: List = None) -> Dict[str, Any]:
        result = ConversationMappers.to_response_dict(conversation)
        if messages is not None:
            result["messages"] = messages
        return result
    
    @staticmethod 
    def summary_to_api_response(summary: ConversationSummary) -> Dict[str, Any]:
        return {
            "session_id": summary.session_id,
            "title": summary.title,
            "message_count": summary.message_count,
            "last_activity": summary.last_activity,
            "document_name": summary.document_name,
            "agent_type": summary.agent_type,
            "tags": summary.tags or []
        }
    
    @staticmethod
    def summaries_to_api_list(summaries: List[ConversationSummary]) -> List[Dict[str, Any]]:
        return [APIResponseMappers.summary_to_api_response(s) for s in summaries]