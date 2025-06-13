# src/ui/components/agent_configuration.py
import streamlit as st
from typing import Optional
from src.agents import AgentManager, AgentType, get_available_agent_types


class AgentConfiguration:

    @staticmethod
    def render_agent_section(rag_system, agent_manager: AgentManager) -> None:
        st.subheader("🤖 Agent Configuration")

        available_docs = rag_system.get_available_documents()
        if not available_docs:
            st.info("Upload documents first to configure agents")
            return

        selected_doc = rag_system.selected_document
        if not selected_doc:
            st.info("Select a document to configure its agent")
            return

        AgentConfiguration._render_current_agent_info(agent_manager, selected_doc)
        AgentConfiguration._render_agent_selector(agent_manager, selected_doc)
        AgentConfiguration._render_custom_instructions(agent_manager, selected_doc)
        AgentConfiguration._render_agent_actions(agent_manager, selected_doc)

    @staticmethod
    def _render_current_agent_info(agent_manager: AgentManager, document_name: str) -> None:
        current_config = agent_manager.get_agent_for_document(document_name)

        if current_config:
            agent_desc = agent_manager.get_agent_description(current_config.agent_type)
            status = "🟢 Active" if current_config.is_active else "🔴 Inactive"
            st.info(f"**Agent actuel:** {agent_desc}\n**Status:** {status}")
        else:
            st.info("**Agent:** Par défaut (Conversationnel)")

    @staticmethod
    def _render_agent_selector(agent_manager: AgentManager, document_name: str) -> None:
        available_agents = get_available_agent_types()
        current_config = agent_manager.get_agent_for_document(document_name)
        current_type = current_config.agent_type.value if current_config else "conversational"

        def handle_agent_change():
            agent_type = AgentType(st.session_state[f"agent_selector_{document_name}"])
            agent_manager.set_agent_for_document(document_name, agent_type)
            st.rerun()

        st.selectbox(
            "Type d'agent:",
            options=list(available_agents.keys()),
            format_func=lambda x: available_agents[x],
            index=list(available_agents.keys()).index(current_type),
            key=f"agent_selector_{document_name}",
            on_change=handle_agent_change
        )

    @staticmethod
    def _render_custom_instructions(agent_manager: AgentManager, document_name: str) -> None:
        current_config = agent_manager.get_agent_for_document(document_name)
        current_instructions = current_config.custom_instructions if current_config else ""

        with st.expander("Instructions personnalisées"):
            new_instructions = st.text_area(
                "Instructions spécifiques pour ce document:",
                value=current_instructions,
                height=100,
                placeholder="Ex: Réponds toujours en bullet points, utilise un ton très technique...",
                key=f"custom_instructions_{document_name}"
            )

            if st.button("Sauvegarder instructions", key=f"save_instructions_{document_name}"):
                if agent_manager.has_agent_configured(document_name):
                    agent_manager.update_custom_instructions(document_name, new_instructions)
                    st.success("Instructions sauvegardées!")
                    st.rerun()
                else:
                    st.error("Configurez d'abord un agent pour ce document")

    @staticmethod
    def _render_agent_actions(agent_manager: AgentManager, document_name: str) -> None:
        if not agent_manager.has_agent_configured(document_name):
            return

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Activer/Désactiver", key=f"toggle_{document_name}"):
                is_active = agent_manager.toggle_agent_active(document_name)
                status = "activé" if is_active else "désactivé"
                st.success(f"Agent {status}!")
                st.rerun()

        with col2:
            if st.button("🗑️ Supprimer agent", key=f"remove_{document_name}"):
                agent_manager.remove_agent_from_document(document_name)
                st.success("Agent supprimé!")
                st.rerun()

    @staticmethod
    def render_agents_overview(agent_manager: AgentManager) -> None:
        st.subheader("📊 Vue d'ensemble des agents")

        stats = agent_manager.get_agent_stats()
        configurations = agent_manager.get_all_document_configurations()

        if stats['total_configured'] == 0:
            st.info("Aucun agent configuré")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Agents configurés", stats['total_configured'])
        with col2:
            st.metric("Agents actifs", stats['active_agents'])
        with col3:
            most_used = stats.get('most_used_agent', 'N/A')
            st.metric("Plus utilisé", most_used)

        if configurations:
            with st.expander("Détail des configurations"):
                for doc_name, config in configurations.items():
                    status_icon = "🟢" if config.is_active else "🔴"
                    agent_name = config.agent_type.value.title()
                    has_custom = "📝" if config.custom_instructions else ""
                    st.text(f"{status_icon} {doc_name}: {agent_name} {has_custom}")

    @staticmethod
    def render_complete_section(rag_system, agent_manager: AgentManager) -> None:
        with st.sidebar:
            AgentConfiguration.render_agent_section(rag_system, agent_manager)

        with st.expander("🤖 Gestion des Agents", expanded=False):
            AgentConfiguration.render_agents_overview(agent_manager)
