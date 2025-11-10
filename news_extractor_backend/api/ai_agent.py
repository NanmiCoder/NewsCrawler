# -*- coding: utf-8 -*-
"""
AI Agent API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from news_extractor_core.ai_agent_service import AIAgentService
from news_extractor_core.ai_agent_models import AgentRequest, AgentResponse

router = APIRouter()


@router.post("/process", response_model=AgentResponse)
async def process_content(request: AgentRequest):
    """
    Process content with AI agent

    Args:
        request: Agent request with LLM config and content

    Returns:
        Agent response with processed result
    """
    try:
        response = await AIAgentService.process(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to process content: {str(e)}"
                }
            }
        )


@router.get("/providers")
async def get_providers() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get list of supported LLM providers

    Returns:
        List of provider information
    """
    return {
        "status": "success",
        "providers": AIAgentService.get_supported_providers()
    }


@router.get("/tasks")
async def get_tasks() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get list of supported task types

    Returns:
        List of task information
    """
    return {
        "status": "success",
        "tasks": AIAgentService.get_supported_tasks()
    }


@router.get("/health")
async def health_check():
    """
    Health check for AI agent service

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "ai_agent"
    }
