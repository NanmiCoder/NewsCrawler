# -*- coding: utf-8 -*-
"""
AI Agent models and configurations
"""
from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"


class LLMConfig(BaseModel):
    """LLM Configuration"""
    provider: LLMProvider = Field(..., description="LLM provider")
    model_name: str = Field(..., description="Model name")
    api_key: str = Field(..., description="API key")
    base_url: Optional[str] = Field(None, description="Custom base URL (optional)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: Optional[int] = Field(default=2000, description="Max tokens")


class AgentTaskType(str, Enum):
    """AI Agent task types"""
    SUMMARIZE = "summarize"
    REWRITE = "rewrite"
    TRANSLATE = "translate"
    EXTRACT_KEYWORDS = "extract_keywords"


class AgentRequest(BaseModel):
    """AI Agent request"""
    llm_config: LLMConfig = Field(..., description="LLM configuration")
    task_type: AgentTaskType = Field(..., description="Task type")
    content: str = Field(..., description="Content to process")
    images: Optional[List[str]] = Field(default=None, description="Image URLs (optional)")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt (optional)")


class AgentResponse(BaseModel):
    """AI Agent response"""
    status: str
    result: Optional[str] = None
    original_content: str
    task_type: str
    provider: str
    model: str
    error: Optional[Dict[str, str]] = None


# Default prompts for different task types
DEFAULT_PROMPTS = {
    AgentTaskType.SUMMARIZE: """Please provide a concise summary of the following content.
Focus on the main points and key information. Keep the summary clear and well-structured.

Content:
{content}

Please provide the summary:""",

    AgentTaskType.REWRITE: """Please rewrite the following content to make it more engaging and easier to read.
Maintain the original meaning but improve the clarity and flow.

Content:
{content}

Please provide the rewritten version:""",

    AgentTaskType.TRANSLATE: """Please translate the following content to English.
Maintain the original tone and meaning.

Content:
{content}

Please provide the translation:""",

    AgentTaskType.EXTRACT_KEYWORDS: """Please extract the main keywords and key phrases from the following content.
List them in order of importance, separated by commas.

Content:
{content}

Please provide the keywords:"""
}
