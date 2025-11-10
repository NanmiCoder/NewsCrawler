# -*- coding: utf-8 -*-
"""
AI Agent Service with multi-LLM support
"""
from typing import Optional, List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from .ai_agent_models import (
    LLMProvider, LLMConfig, AgentRequest, AgentResponse,
    AgentTaskType, DEFAULT_PROMPTS
)
from .image_utils import ImageProcessor


class AIAgentService:
    """AI Agent Service for content processing"""

    @staticmethod
    def _create_llm(config: LLMConfig) -> BaseChatModel:
        """
        Create LLM instance based on provider

        Args:
            config: LLM configuration

        Returns:
            LangChain LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        common_params = {
            "model": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        # OpenAI and compatible providers (DeepSeek, Qwen, Kimi)
        if config.provider in [LLMProvider.OPENAI, LLMProvider.DEEPSEEK,
                               LLMProvider.QWEN, LLMProvider.KIMI]:
            llm_params = {
                **common_params,
                "api_key": config.api_key,
            }
            if config.base_url:
                llm_params["base_url"] = config.base_url

            # Set default base URLs for known providers
            if config.provider == LLMProvider.DEEPSEEK and not config.base_url:
                llm_params["base_url"] = "https://api.deepseek.com/v1"
            elif config.provider == LLMProvider.QWEN and not config.base_url:
                llm_params["base_url"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif config.provider == LLMProvider.KIMI and not config.base_url:
                llm_params["base_url"] = "https://api.moonshot.cn/v1"

            return ChatOpenAI(**llm_params)

        # Anthropic
        elif config.provider == LLMProvider.ANTHROPIC:
            llm_params = {
                **common_params,
                "anthropic_api_key": config.api_key,
            }
            if config.base_url:
                llm_params["anthropic_api_url"] = config.base_url
            return ChatAnthropic(**llm_params)

        # Google Gemini
        elif config.provider == LLMProvider.GEMINI:
            return ChatGoogleGenerativeAI(
                model=config.model_name,
                google_api_key=config.api_key,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
            )

        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    @staticmethod
    def _build_prompt(task_type: AgentTaskType, content: str, custom_prompt: Optional[str] = None) -> str:
        """
        Build prompt for the task

        Args:
            task_type: Task type
            content: Content to process
            custom_prompt: Custom prompt (optional)

        Returns:
            Formatted prompt
        """
        if custom_prompt:
            return custom_prompt.format(content=content)
        else:
            template = DEFAULT_PROMPTS.get(task_type, DEFAULT_PROMPTS[AgentTaskType.SUMMARIZE])
            return template.format(content=content)

    @staticmethod
    async def _prepare_images(image_urls: Optional[List[str]]) -> List[Dict[str, Any]]:
        """
        Download and encode images for vision models

        Args:
            image_urls: List of image URLs

        Returns:
            List of image data dictionaries for LangChain
        """
        if not image_urls:
            return []

        image_data = []
        for url in image_urls:
            try:
                base64_image = await ImageProcessor.download_and_encode(url)
                if base64_image:
                    # Format for LangChain vision models
                    image_data.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
            except Exception as e:
                print(f"Failed to process image {url}: {e}")
                continue

        return image_data

    @staticmethod
    async def process(request: AgentRequest) -> AgentResponse:
        """
        Process content with AI agent

        Args:
            request: Agent request

        Returns:
            Agent response

        Raises:
            Exception: If processing fails
        """
        try:
            # Create LLM instance
            llm = AIAgentService._create_llm(request.llm_config)

            # Build prompt
            prompt_text = AIAgentService._build_prompt(
                request.task_type,
                request.content,
                request.custom_prompt
            )

            # Prepare messages
            messages = []

            # Add system message for context
            system_msg = "You are a helpful AI assistant that processes content accurately and professionally."
            messages.append(SystemMessage(content=system_msg))

            # Check if images are provided and if the model supports vision
            if request.images:
                # Process images
                image_data = await AIAgentService._prepare_images(request.images)

                # Create multimodal message
                content_parts = [{"type": "text", "text": prompt_text}]
                content_parts.extend(image_data)

                messages.append(HumanMessage(content=content_parts))
            else:
                # Text-only message
                messages.append(HumanMessage(content=prompt_text))

            # Invoke LLM
            response = await llm.ainvoke(messages)

            # Extract result
            result_text = response.content if hasattr(response, 'content') else str(response)

            return AgentResponse(
                status="success",
                result=result_text,
                original_content=request.content,
                task_type=request.task_type.value,
                provider=request.llm_config.provider.value,
                model=request.llm_config.model_name,
            )

        except Exception as e:
            error_message = str(e)
            print(f"AI Agent processing failed: {error_message}")

            return AgentResponse(
                status="error",
                result=None,
                original_content=request.content,
                task_type=request.task_type.value,
                provider=request.llm_config.provider.value,
                model=request.llm_config.model_name,
                error={
                    "code": "PROCESSING_FAILED",
                    "message": error_message
                }
            )

    @staticmethod
    def get_supported_providers() -> List[Dict[str, str]]:
        """
        Get list of supported LLM providers

        Returns:
            List of provider information
        """
        return [
            {
                "id": LLMProvider.OPENAI.value,
                "name": "OpenAI",
                "default_model": "gpt-4o",
                "supports_vision": True,
            },
            {
                "id": LLMProvider.ANTHROPIC.value,
                "name": "Anthropic Claude",
                "default_model": "claude-3-5-sonnet-20241022",
                "supports_vision": True,
            },
            {
                "id": LLMProvider.GEMINI.value,
                "name": "Google Gemini",
                "default_model": "gemini-2.0-flash",
                "supports_vision": True,
            },
            {
                "id": LLMProvider.DEEPSEEK.value,
                "name": "DeepSeek",
                "default_model": "deepseek-chat",
                "supports_vision": False,
            },
            {
                "id": LLMProvider.QWEN.value,
                "name": "Alibaba Qwen",
                "default_model": "qwen-plus",
                "supports_vision": False,
            },
            {
                "id": LLMProvider.KIMI.value,
                "name": "Moonshot Kimi",
                "default_model": "moonshot-v1-8k",
                "supports_vision": False,
            },
        ]

    @staticmethod
    def get_supported_tasks() -> List[Dict[str, str]]:
        """
        Get list of supported task types

        Returns:
            List of task information
        """
        return [
            {
                "id": AgentTaskType.SUMMARIZE.value,
                "name": "Summarize",
                "description": "Generate a concise summary of the content",
                "icon": "📝"
            },
            {
                "id": AgentTaskType.REWRITE.value,
                "name": "Rewrite",
                "description": "Rewrite the content for better clarity",
                "icon": "✨"
            },
            {
                "id": AgentTaskType.TRANSLATE.value,
                "name": "Translate",
                "description": "Translate content to English",
                "icon": "🌐"
            },
            {
                "id": AgentTaskType.EXTRACT_KEYWORDS.value,
                "name": "Extract Keywords",
                "description": "Extract main keywords and phrases",
                "icon": "🔑"
            },
        ]
