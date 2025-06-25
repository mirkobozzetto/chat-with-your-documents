# src/ui/components/agent_configuration.py
import streamlit as st
from typing import Optional
from src.agents import AgentManager, AgentType, get_available_agent_types


class AgentConfiguration:

    @staticmethod
    def render_agent_section(rag_system, agent_manager: AgentManager) -> None:
        st.subheader("Agent Configuration")

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
            status = "Active" if current_config.is_active else "Inactive"
            st.info(f"**Current agent:** {agent_desc}\n**Status:** {status}")
        else:
            st.info("**Agent:** Default (Conversationnel)")

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
            "Agent type:",
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
                placeholder="Ex: Always respond in bullet points, use a very technical tone...",
                key=f"custom_instructions_{document_name}"
            )

            if st.button("Save instructions", key=f"save_instructions_{document_name}"):
                if agent_manager.has_agent_configured(document_name):
                    agent_manager.update_custom_instructions(document_name, new_instructions)
                    st.success("Instructions saved!")
                    st.rerun()
                else:
                    st.error("Configure an agent for this document first")

    @staticmethod
    def _render_agent_actions(agent_manager: AgentManager, document_name: str) -> None:
        if not agent_manager.has_agent_configured(document_name):
            return

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Activate/Deactivate", key=f"toggle_{document_name}"):
                is_active = agent_manager.toggle_agent_active(document_name)
                status = "activated" if is_active else "deactivated"
                st.success(f"Agent {status}!")
                st.rerun()

        with col2:
            if st.button("🗑️ Delete agent", key=f"remove_{document_name}"):
                agent_manager.remove_agent_from_document(document_name)
                st.success("Agent deleted!")
                st.rerun()

    @staticmethod
    def render_agents_overview(agent_manager: AgentManager) -> None:
        st.subheader("Agent Overview")

        stats = agent_manager.get_agent_stats()
        configurations = agent_manager.get_all_document_configurations()

        if stats['total_configured'] == 0:
            st.info("No agent configured")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Configured agents", stats['total_configured'])
        with col2:
            st.metric("Active agents", stats['active_agents'])
        with col3:
            most_used = stats.get('most_used_agent', 'N/A')
            st.metric("Most used", most_used)

        if configurations:
            with st.expander("Configuration details"):
                for doc_name, config in configurations.items():
                    status_icon = "🟢" if config.is_active else "🔴"
                    agent_name = config.agent_type.value.title()
                    has_custom = "📝" if config.custom_instructions else ""
                    st.text(f"{status_icon} {doc_name}: {agent_name} {has_custom}")

    @staticmethod
    def render_complete_section(rag_system, agent_manager: AgentManager) -> None:
        with st.sidebar:
            AgentConfiguration.render_agent_section(rag_system, agent_manager)

        with st.expander("Agent Management", expanded=False):
            AgentConfiguration.render_agents_overview(agent_manager)
