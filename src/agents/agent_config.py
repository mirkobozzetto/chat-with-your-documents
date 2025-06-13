# src/agents/agent_config.py
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import json
import os
from .agent_types import AgentType


@dataclass
class AgentConfiguration:
    document_name: str
    agent_type: AgentType
    custom_instructions: Optional[str] = None
    is_active: bool = True


class AgentConfigManager:
    def __init__(self, config_file: str = "agent_configs.json"):
        self.config_file = config_file
        self.configurations: Dict[str, AgentConfiguration] = {}
        self.load_configurations()

    def load_configurations(self) -> None:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc_name, config_data in data.items():
                        agent_type = AgentType(config_data['agent_type'])
                        self.configurations[doc_name] = AgentConfiguration(
                            document_name=doc_name,
                            agent_type=agent_type,
                            custom_instructions=config_data.get('custom_instructions'),
                            is_active=config_data.get('is_active', True)
                        )
            except (json.JSONDecodeError, KeyError, ValueError):
                self.configurations = {}

    def save_configurations(self) -> None:
        data = {}
        for doc_name, config in self.configurations.items():
            data[doc_name] = {
                'agent_type': config.agent_type.value,
                'custom_instructions': config.custom_instructions,
                'is_active': config.is_active
            }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def set_agent_for_document(self, document_name: str, agent_type: AgentType,
                              custom_instructions: Optional[str] = None) -> None:
        self.configurations[document_name] = AgentConfiguration(
            document_name=document_name,
            agent_type=agent_type,
            custom_instructions=custom_instructions
        )
        self.save_configurations()

    def get_agent_for_document(self, document_name: str) -> Optional[AgentConfiguration]:
        return self.configurations.get(document_name)

    def remove_agent_for_document(self, document_name: str) -> None:
        if document_name in self.configurations:
            del self.configurations[document_name]
            self.save_configurations()

    def get_all_configurations(self) -> Dict[str, AgentConfiguration]:
        return self.configurations.copy()

    def has_agent_configured(self, document_name: str) -> bool:
        return document_name in self.configurations

    def update_custom_instructions(self, document_name: str, instructions: str) -> None:
        if document_name in self.configurations:
            self.configurations[document_name].custom_instructions = instructions
            self.save_configurations()

    def toggle_agent_active(self, document_name: str) -> bool:
        if document_name in self.configurations:
            config = self.configurations[document_name]
            config.is_active = not config.is_active
            self.save_configurations()
            return config.is_active
        return False

    def get_default_agent_type(self) -> AgentType:
        return AgentType.CONVERSATIONAL

    def cleanup_unused_documents(self, active_documents: list) -> None:
        documents_to_remove = []
        for doc_name in self.configurations.keys():
            if doc_name not in active_documents:
                documents_to_remove.append(doc_name)

        for doc_name in documents_to_remove:
            self.remove_agent_for_document(doc_name)
