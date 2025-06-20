# src/api/routers/agents.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from src.api.models.agent_models import (
    AgentConfigRequest,
    AgentConfigResponse,
    AgentStatsResponse,
    AgentOverviewResponse,
)

from src.api.dependencies.rag_system import get_user_rag_system
from src.api.dependencies.authentication import get_optional_current_user
from src.api.models.auth_models import UserInfo
from src.rag_system import RAGOrchestrator
from src.agents import get_available_agent_types, get_agent_behavior



router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/types")
async def get_agent_types():
    available_types = get_available_agent_types()
    type_details = {}

    for agent_type, name in available_types.items():
        try:
            from src.agents.agent_types import AgentType
            behavior = get_agent_behavior(AgentType(agent_type))
            type_details[agent_type] = {
                "name": name,
                "description": behavior.description,
                "tone": behavior.tone,
                "response_style": behavior.response_style,
                "use_cases": behavior.use_cases
            }
        except:
            type_details[agent_type] = {"name": name}

    return {
        "available_types": available_types,
        "type_details": type_details
    }


@router.post("/configure", response_model=AgentConfigResponse)
async def configure_agent(
    request: AgentConfigRequest,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if request.document_name not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{request.document_name}' not found"
            )

        agent_manager = rag_system.qa_manager.get_agent_manager()

        agent_config = agent_manager.configure_agent(
            document_name=request.document_name,
            agent_type=request.agent_type.value,
            custom_instructions=request.custom_instructions,
            is_active=request.is_active
        )

        from src.agents.agent_types import AgentType
        behavior = get_agent_behavior(AgentType(request.agent_type.value))

        return AgentConfigResponse(
            document_name=request.document_name,
            agent_type=request.agent_type.value,
            custom_instructions=request.custom_instructions,
            is_active=request.is_active,
            agent_behavior={
                "name": behavior.name,
                "description": behavior.description,
                "tone": behavior.tone,
                "response_style": behavior.response_style,
                "use_cases": behavior.use_cases
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error configuring agent: {str(e)}"
        )


@router.get("/", response_model=AgentOverviewResponse)
async def get_agents_overview(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        agent_manager = rag_system.qa_manager.get_agent_manager()
        available_docs = rag_system.get_available_documents()

        agents = []
        for doc_name in available_docs:
            agent_config = agent_manager.get_agent_for_document(doc_name)
            if agent_config:
                try:
                    from src.agents.agent_types import AgentType
                    behavior = get_agent_behavior(agent_config.agent_type)
                    agent_behavior = {
                        "name": behavior.name,
                        "description": behavior.description,
                        "tone": behavior.tone,
                        "response_style": behavior.response_style,
                        "use_cases": behavior.use_cases
                    }
                except:
                    agent_behavior = {}

                agents.append(AgentConfigResponse(
                    document_name=doc_name,
                    agent_type=agent_config.agent_type.value,
                    custom_instructions=agent_config.custom_instructions,
                    is_active=agent_config.is_active,
                    agent_behavior=agent_behavior
                ))

        active_agents = sum(1 for agent in agents if agent.is_active)

        agent_distribution = {}
        for agent in agents:
            agent_type = agent.agent_type
            agent_distribution[agent_type] = agent_distribution.get(agent_type, 0) + 1

        most_used_type = max(agent_distribution.items(), key=lambda x: x[1])[0] if agent_distribution else None

        stats = AgentStatsResponse(
            total_agents=len(agents),
            active_agents=active_agents,
            most_used_agent_type=most_used_type,
            agent_distribution=agent_distribution
        )

        return AgentOverviewResponse(
            agents=agents,
            stats=stats,
            available_types=get_available_agent_types()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents overview: {str(e)}"
        )


@router.get("/{document_name}", response_model=AgentConfigResponse)
async def get_agent_config(
    document_name: str,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if document_name not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_name}' not found"
            )

        agent_manager = rag_system.qa_manager.get_agent_manager()
        agent_config = agent_manager.get_agent_for_document(document_name)

        if not agent_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No agent configured for document '{document_name}'"
            )

        try:
            from src.agents.agent_types import AgentType
            behavior = get_agent_behavior(agent_config.agent_type)
            agent_behavior = {
                "name": behavior.name,
                "description": behavior.description,
                "tone": behavior.tone,
                "response_style": behavior.response_style,
                "use_cases": behavior.use_cases
            }
        except:
            agent_behavior = {}

        return AgentConfigResponse(
            document_name=document_name,
            agent_type=agent_config.agent_type.value,
            custom_instructions=agent_config.custom_instructions,
            is_active=agent_config.is_active,
            agent_behavior=agent_behavior
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent config: {str(e)}"
        )


@router.delete("/{document_name}")
async def remove_agent_config(
    document_name: str,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if document_name not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_name}' not found"
            )

        agent_manager = rag_system.qa_manager.get_agent_manager()
        success = agent_manager.remove_agent(document_name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No agent configured for document '{document_name}'"
            )

        return {"message": f"Agent configuration removed for document '{document_name}'"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing agent config: {str(e)}"
        )


@router.patch("/{document_name}/toggle")
async def toggle_agent_status(
    document_name: str,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if document_name not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_name}' not found"
            )

        agent_manager = rag_system.qa_manager.get_agent_manager()
        agent_config = agent_manager.get_agent_for_document(document_name)

        if not agent_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No agent configured for document '{document_name}'"
            )

        new_status = not agent_config.is_active
        updated_config = agent_manager.configure_agent(
            document_name=document_name,
            agent_type=agent_config.agent_type.value,
            custom_instructions=agent_config.custom_instructions,
            is_active=new_status
        )

        return {
            "message": f"Agent status {'activated' if new_status else 'deactivated'} for document '{document_name}'",
            "is_active": new_status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling agent status: {str(e)}"
        )
