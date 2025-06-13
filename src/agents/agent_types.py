# src/agents/agent_types.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class AgentType(Enum):
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    COMMERCIAL = "commercial"
    ANALYTICAL = "analytical"
    EDUCATIONAL = "educational"
    CREATIVE = "creative"


@dataclass
class AgentBehavior:
    name: str
    description: str
    tone: str
    response_style: str
    use_cases: list


AGENT_BEHAVIORS = {
    AgentType.CONVERSATIONAL: AgentBehavior(
        name="Agent Conversationnel",
        description="Répond de manière naturelle et accessible",
        tone="friendly_casual",
        response_style="dialogue_natural",
        use_cases=["FAQ", "Support client", "Chat général"]
    ),

    AgentType.TECHNICAL: AgentBehavior(
        name="Agent Technique",
        description="Expert technique avec réponses détaillées",
        tone="professional_precise",
        response_style="structured_detailed",
        use_cases=["Documentation", "Troubleshooting", "Spécifications"]
    ),

    AgentType.COMMERCIAL: AgentBehavior(
        name="Agent Commercial",
        description="Orienté vente et persuasion",
        tone="confident_persuasive",
        response_style="benefits_focused",
        use_cases=["Pitch", "Démonstration", "Objections"]
    ),

    AgentType.ANALYTICAL: AgentBehavior(
        name="Agent Analytique",
        description="Analyse approfondie avec données",
        tone="objective_analytical",
        response_style="data_driven",
        use_cases=["Rapports", "Analyses", "Comparaisons"]
    ),

    AgentType.EDUCATIONAL: AgentBehavior(
        name="Agent Pédagogique",
        description="Explique de manière claire et progressive",
        tone="patient_encouraging",
        response_style="step_by_step",
        use_cases=["Formation", "Tutoriels", "Apprentissage"]
    ),

    AgentType.CREATIVE: AgentBehavior(
        name="Agent Créatif",
        description="Approche imaginative et innovante",
        tone="inspiring_creative",
        response_style="imaginative_storytelling",
        use_cases=["Brainstorming", "Copywriting", "Innovation"]
    )
}


def get_agent_behavior(agent_type: AgentType) -> AgentBehavior:
    return AGENT_BEHAVIORS[agent_type]


def get_available_agent_types() -> Dict[str, str]:
    return {agent_type.value: behavior.name for agent_type, behavior in AGENT_BEHAVIORS.items()}


def get_agent_type_from_string(type_string: str) -> AgentType:
    return AgentType(type_string)
