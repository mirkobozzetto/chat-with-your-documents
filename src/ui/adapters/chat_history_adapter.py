# src/ui/adapters/chat_history_adapter.py
import streamlit as st
from typing import List, Dict, Any, Optional
from src.chat_history.session_manager import SessionManager, ConversationHistoryManager
from src.chat_history.models import Conversation


class StreamlitChatHistoryAdapter:

    def __init__(self):
        self.session_manager = self._get_session_manager()
        self.history_manager = ConversationHistoryManager()
        self._sync_with_streamlit_state()

    def _get_session_manager(self) -> SessionManager:
        if 'chat_session_manager' not in st.session_state:
            st.session_state.chat_session_manager = SessionManager()
            st.session_state.chat_session_manager.set_session_change_callback(
                self._on_session_change
            )
        return st.session_state.chat_session_manager

    def _sync_with_streamlit_state(self) -> None:
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        current_session = self.session_manager.get_current_session()
        if current_session:
            st.session_state.messages = [
                {"role": msg.role, "content": msg.content}
                for msg in current_session.messages
            ]

    def _on_session_change(self, conversation: Optional[Conversation]) -> None:
        if conversation:
            st.session_state.messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation.messages
            ]
        else:
            st.session_state.messages = []

    def add_message(self, role: str, content: str, **metadata) -> None:
        self.session_manager.add_message(role, content, metadata)

        if {"role": role, "content": content} not in st.session_state.messages:
            st.session_state.messages.append({"role": role, "content": content})

    def clear_current_conversation(self) -> None:
        self.session_manager.clear_current_session_messages()
        st.session_state.messages = []

    def start_new_conversation(self, title: str = "New Conversation", **metadata) -> str:
        conversation = self.session_manager.create_new_session(title=title, **metadata)
        st.session_state.messages = []
        return conversation.session_id

    def load_conversation(self, session_id: str) -> bool:
        conversation = self.session_manager.load_session(session_id)
        if conversation:
            st.session_state.messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation.messages
            ]
            return True
        return False

    def update_conversation_context(self, document_name: str = None, agent_type: str = None) -> None:
        metadata_updates = {}
        if document_name:
            metadata_updates["document_name"] = document_name
        if agent_type:
            metadata_updates["agent_type"] = agent_type

        if metadata_updates:
            self.session_manager.update_session_metadata(**metadata_updates)

    def get_current_session_id(self) -> Optional[str]:
        return self.session_manager.get_session_id()

    def get_current_conversation_info(self) -> Optional[Dict[str, Any]]:
        current_session = self.session_manager.get_current_session()
        if current_session:
            return {
                "session_id": current_session.session_id,
                "title": current_session.title,
                "message_count": current_session.message_count,
                "document_name": current_session.metadata.document_name,
                "agent_type": current_session.metadata.agent_type,
                "created_at": current_session.created_at,
                "last_activity": current_session.last_activity
            }
        return None

    def list_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.history_manager.list_recent_conversations(limit)

    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        return self.history_manager.search_conversations(query)

    def delete_conversation(self, session_id: str) -> bool:
        success = self.history_manager.delete_conversation(session_id)
        if success and self.get_current_session_id() == session_id:
            st.session_state.messages = []
        return success

    def export_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.history_manager.export_conversation(session_id)

    def get_conversations_for_document(self, document_name: str) -> List[Dict[str, Any]]:
        return self.history_manager.get_conversations_by_document(document_name)

    def has_active_conversation(self) -> bool:
        return self.session_manager.has_active_session()

    def get_conversation_statistics(self) -> Dict[str, Any]:
        return self.history_manager.get_statistics()

    def render_conversation_sidebar(self) -> None:
        st.subheader("💬 Historique des conversations")

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("➕ Nouvelle conversation"):
                self.start_new_conversation()
                st.rerun()

        with col2:
            if st.button("🗑️"):
                if self.has_active_conversation():
                    session_id = self.get_current_session_id()
                    if session_id and self.delete_conversation(session_id):
                        st.success("Conversation supprimée")
                        st.rerun()

        search_query = st.text_input("🔍 Rechercher...", placeholder="Tapez pour rechercher")

        if search_query:
            conversations = self.search_conversations(search_query)
        else:
            conversations = self.list_recent_conversations(limit=15)

        current_session_id = self.get_current_session_id()

        if conversations:
            st.write("**Conversations récentes:**")
            for conv in conversations:
                is_current = conv["session_id"] == current_session_id
                title_display = conv["title"][:40] + ("..." if len(conv["title"]) > 40 else "")

                button_style = "🔵" if is_current else "⚪"
                button_text = f"{button_style} {title_display}"

                if st.button(button_text, key=f"conv_{conv['session_id']}",
                           help=f"Messages: {conv['message_count']} | {conv['last_activity'].strftime('%d/%m %H:%M')}"):
                    if not is_current:
                        self.load_conversation(conv["session_id"])
                        st.rerun()
        else:
            st.info("Aucune conversation trouvée")

        current_info = self.get_current_conversation_info()
        if current_info:
            with st.expander("ℹ️ Conversation actuelle"):
                st.text(f"Titre: {current_info['title']}")
                st.text(f"Messages: {current_info['message_count']}")
                if current_info['document_name']:
                    st.text(f"Document: {current_info['document_name']}")
                if current_info['agent_type']:
                    st.text(f"Agent: {current_info['agent_type']}")

    def render_conversation_management(self) -> None:
        with st.expander("📋 Gestion des conversations"):
            stats = self.get_conversation_statistics()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total conversations", stats["total_conversations"])
            with col2:
                st.metric("Cette semaine", stats["recent_conversations"])

            if st.button("🧹 Nettoyer anciennes (30j+)"):
                deleted = self.history_manager.cleanup_old_conversations()
                st.success(f"{deleted} conversations supprimées")
                st.rerun()
