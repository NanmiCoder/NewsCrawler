# -*- coding: utf-8 -*-
"""
Unit tests for AI Agent API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_extractor_backend.main import app

client = TestClient(app)


class TestAIAgentEndpoints:
    """Test AI Agent API endpoints"""

    def test_get_providers(self):
        """Test getting list of LLM providers"""
        response = client.get("/api/agent/providers")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "providers" in data
        assert len(data["providers"]) == 6

        # Check provider structure
        provider = data["providers"][0]
        assert "id" in provider
        assert "name" in provider
        assert "default_model" in provider
        assert "supports_vision" in provider

    def test_get_tasks(self):
        """Test getting list of task types"""
        response = client.get("/api/agent/tasks")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "tasks" in data
        assert len(data["tasks"]) == 4

        # Check task structure
        task = data["tasks"][0]
        assert "id" in task
        assert "name" in task
        assert "description" in task
        assert "icon" in task

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/agent/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "ai_agent"

    @patch('news_extractor_core.ai_agent_service.AIAgentService.process')
    @pytest.mark.asyncio
    async def test_process_content_success(self, mock_process):
        """Test successful content processing"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = "success"
        mock_response.result = "This is a test summary"
        mock_response.original_content = "Test content"
        mock_response.task_type = "summarize"
        mock_response.provider = "openai"
        mock_response.model = "gpt-4o"
        mock_response.error = None

        mock_process.return_value = mock_response

        # Make request
        request_data = {
            "llm_config": {
                "provider": "openai",
                "model_name": "gpt-4o",
                "api_key": "test-key",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "task_type": "summarize",
            "content": "Test content to summarize"
        }

        response = client.post("/api/agent/process", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["result"] == "This is a test summary"
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"

    def test_process_content_missing_fields(self):
        """Test processing with missing required fields"""
        request_data = {
            "llm_config": {
                "provider": "openai",
                # Missing model_name and api_key
            },
            "task_type": "summarize",
            "content": "Test content"
        }

        response = client.post("/api/agent/process", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    def test_process_content_invalid_provider(self):
        """Test processing with invalid provider"""
        request_data = {
            "llm_config": {
                "provider": "invalid_provider",
                "model_name": "test-model",
                "api_key": "test-key"
            },
            "task_type": "summarize",
            "content": "Test content"
        }

        response = client.post("/api/agent/process", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    def test_process_content_invalid_task(self):
        """Test processing with invalid task type"""
        request_data = {
            "llm_config": {
                "provider": "openai",
                "model_name": "gpt-4o",
                "api_key": "test-key"
            },
            "task_type": "invalid_task",
            "content": "Test content"
        }

        response = client.post("/api/agent/process", json=request_data)

        # Should return validation error
        assert response.status_code == 422


class TestAIAgentService:
    """Test AI Agent Service logic"""

    def test_get_supported_providers(self):
        """Test getting supported providers"""
        from news_extractor_core.ai_agent_service import AIAgentService

        providers = AIAgentService.get_supported_providers()

        assert len(providers) == 6
        assert any(p["id"] == "openai" for p in providers)
        assert any(p["id"] == "anthropic" for p in providers)
        assert any(p["id"] == "gemini" for p in providers)
        assert any(p["id"] == "deepseek" for p in providers)
        assert any(p["id"] == "qwen" for p in providers)
        assert any(p["id"] == "kimi" for p in providers)

    def test_get_supported_tasks(self):
        """Test getting supported tasks"""
        from news_extractor_core.ai_agent_service import AIAgentService

        tasks = AIAgentService.get_supported_tasks()

        assert len(tasks) == 4
        assert any(t["id"] == "summarize" for t in tasks)
        assert any(t["id"] == "rewrite" for t in tasks)
        assert any(t["id"] == "translate" for t in tasks)
        assert any(t["id"] == "extract_keywords" for t in tasks)

    def test_build_prompt_default(self):
        """Test building default prompt"""
        from news_extractor_core.ai_agent_service import AIAgentService
        from news_extractor_core.ai_agent_models import AgentTaskType

        content = "This is test content"
        prompt = AIAgentService._build_prompt(AgentTaskType.SUMMARIZE, content)

        assert content in prompt
        assert "summary" in prompt.lower()

    def test_build_prompt_custom(self):
        """Test building custom prompt"""
        from news_extractor_core.ai_agent_service import AIAgentService
        from news_extractor_core.ai_agent_models import AgentTaskType

        content = "This is test content"
        custom_prompt = "Custom instruction: {content}"
        prompt = AIAgentService._build_prompt(
            AgentTaskType.SUMMARIZE,
            content,
            custom_prompt
        )

        assert content in prompt
        assert "Custom instruction" in prompt


class TestImageUtils:
    """Test image processing utilities"""

    def test_get_image_mime_type(self):
        """Test getting MIME type for image formats"""
        from news_extractor_core.image_utils import ImageProcessor

        assert ImageProcessor.get_image_mime_type("JPEG") == "image/jpeg"
        assert ImageProcessor.get_image_mime_type("PNG") == "image/png"
        assert ImageProcessor.get_image_mime_type("GIF") == "image/gif"
        assert ImageProcessor.get_image_mime_type("WEBP") == "image/webp"

    def test_create_data_uri(self):
        """Test creating data URI"""
        from news_extractor_core.image_utils import ImageProcessor

        base64_str = "abcd1234"
        uri = ImageProcessor.create_data_uri(base64_str, "JPEG")

        assert uri.startswith("data:image/jpeg;base64,")
        assert "abcd1234" in uri


class TestAIAgentModels:
    """Test AI Agent models"""

    def test_llm_config_validation(self):
        """Test LLM config validation"""
        from news_extractor_core.ai_agent_models import LLMConfig, LLMProvider

        # Valid config
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4o",
            api_key="test-key"
        )

        assert config.provider == LLMProvider.OPENAI
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.7  # default
        assert config.max_tokens == 2000  # default

    def test_llm_config_custom_values(self):
        """Test LLM config with custom values"""
        from news_extractor_core.ai_agent_models import LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            api_key="test-key",
            base_url="https://custom.api.com",
            temperature=0.5,
            max_tokens=4000
        )

        assert config.base_url == "https://custom.api.com"
        assert config.temperature == 0.5
        assert config.max_tokens == 4000

    def test_agent_request_validation(self):
        """Test agent request validation"""
        from news_extractor_core.ai_agent_models import (
            AgentRequest, LLMConfig, LLMProvider, AgentTaskType
        )

        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4o",
            api_key="test-key"
        )

        request = AgentRequest(
            llm_config=llm_config,
            task_type=AgentTaskType.SUMMARIZE,
            content="Test content"
        )

        assert request.task_type == AgentTaskType.SUMMARIZE
        assert request.content == "Test content"
        assert request.images is None

    def test_agent_request_with_images(self):
        """Test agent request with images"""
        from news_extractor_core.ai_agent_models import (
            AgentRequest, LLMConfig, LLMProvider, AgentTaskType
        )

        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4o",
            api_key="test-key"
        )

        request = AgentRequest(
            llm_config=llm_config,
            task_type=AgentTaskType.SUMMARIZE,
            content="Test content",
            images=["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
        )

        assert len(request.images) == 2
        assert request.images[0] == "https://example.com/image1.jpg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
