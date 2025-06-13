# src/agents/agent_manager.py
from typing import Optional, List, Dict, Any
from .agent_types import AgentType, get_agent_behavior
from .prompt_templates import build_prompt
from .agent_config import AgentConfigManager, AgentConfiguration


class AgentManager:
    def __init__(self):
        self.config_manager = AgentConfigManager()

    def get_agent_for_document(self, document_name: Optional[str]) -> Optional[AgentConfiguration]:
        if not document_name:
            return None
        return self.config_manager.get_agent_for_document(document_name)

    def set_agent_for_document(self, document_name: str, agent_type: AgentType,
                              custom_instructions: Optional[str] = None) -> None:
        self.config_manager.set_agent_for_document(document_name, agent_type, custom_instructions)

    def build_enhanced_prompt(self, question: str, context: str,
                            document_name: Optional[str] = None) -> str:
        agent_config = self.get_agent_for_document(document_name)

        if not agent_config or not agent_config.is_active:
            return self._build_default_prompt(question, context)

        return build_prompt(
            agent_type=agent_config.agent_type,
            context=context,
            question=question,
            custom_instructions=agent_config.custom_instructions
        )

    def _build_default_prompt(self, question: str, context: str) -> str:
        default_type = self.config_manager.get_default_agent_type()
        return build_prompt(default_type, context, question)

    def get_available_agents(self) -> Dict[str, str]:
        from .agent_types import get_available_agent_types
        return get_available_agent_types()

    def get_agent_description(self, agent_type: AgentType) -> str:
        behavior = get_agent_behavior(agent_type)
        return f"{behavior.name}: {behavior.description}"

    def get_all_document_configurations(self) -> Dict[str, AgentConfiguration]:
        return self.config_manager.get_all_configurations()

    def remove_agent_from_document(self, document_name: str) -> None:
        self.config_manager.remove_agent_for_document(document_name)

    def update_custom_instructions(self, document_name: str, instructions: str) -> None:
        self.config_manager.update_custom_instructions(document_name, instructions)

    def has_agent_configured(self, document_name: str) -> bool:
        return self.config_manager.has_agent_configured(document_name)

    def toggle_agent_active(self, document_name: str) -> bool:
        return self.config_manager.toggle_agent_active(document_name)

    def sync_with_available_documents(self, available_documents: List[str]) -> None:
        self.config_manager.cleanup_unused_documents(available_documents)

    def get_agent_stats(self) -> Dict[str, Any]:
        configs = self.get_all_document_configurations()

        agent_counts = {}
        active_agents = 0

        for config in configs.values():
            agent_type = config.agent_type.value
            agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
            if config.is_active:
                active_agents += 1

        return {
            'total_configured': len(configs),
            'active_agents': active_agents,
            'agent_distribution': agent_counts,
            'most_used_agent': max(agent_counts.items(), key=lambda x: x[1])[0] if agent_counts else None
        }

    def export_configurations(self) -> Dict[str, Any]:
        configs = self.get_all_document_configurations()
        return {
            doc_name: {
                'agent_type': config.agent_type.value,
                'custom_instructions': config.custom_instructions,
                'is_active': config.is_active,
                'description': self.get_agent_description(config.agent_type)
            }
            for doc_name, config in configs.items()
        }

    def import_configurations(self, config_data: Dict[str, Any]) -> None:
        for doc_name, config_info in config_data.items():
            try:
                agent_type = AgentType(config_info['agent_type'])
                self.set_agent_for_document(
                    doc_name,
                    agent_type,
                    config_info.get('custom_instructions')
                )
            except (KeyError, ValueError):
                continue
