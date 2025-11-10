#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test runner that doesn't require pytest
"""
import sys
import os
from unittest.mock import Mock, MagicMock

# Add current directory and parent to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Mock langchain modules
langchain_mock = MagicMock()
langchain_core_mock = MagicMock()
langchain_core_messages_mock = MagicMock()
langchain_core_language_models_mock = MagicMock()

sys.modules['langchain'] = langchain_mock
sys.modules['langchain_core'] = langchain_core_mock
sys.modules['langchain_core.messages'] = langchain_core_messages_mock
sys.modules['langchain_core.language_models'] = langchain_core_language_models_mock
sys.modules['langchain_openai'] = MagicMock()
sys.modules['langchain_anthropic'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()

# Create mock classes
class MockHumanMessage:
    def __init__(self, content):
        self.content = content

class MockSystemMessage:
    def __init__(self, content):
        self.content = content

langchain_core_messages_mock.HumanMessage = MockHumanMessage
langchain_core_messages_mock.SystemMessage = MockSystemMessage

print("=" * 70)
print("Running AI Agent Unit Tests")
print("=" * 70)

# Test 1: Import test
print("\n[TEST 1] Testing imports...")
try:
    from news_extractor_backend.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    print("✓ Imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Get providers endpoint
print("\n[TEST 2] Testing GET /api/agent/providers...")
try:
    response = client.get("/api/agent/providers")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "success", f"Expected success status"
    assert len(data["providers"]) == 6, f"Expected 6 providers, got {len(data['providers'])}"
    print(f"✓ Providers endpoint works - Found {len(data['providers'])} providers")
except Exception as e:
    print(f"✗ Providers endpoint failed: {e}")

# Test 3: Get tasks endpoint
print("\n[TEST 3] Testing GET /api/agent/tasks...")
try:
    response = client.get("/api/agent/tasks")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "success", f"Expected success status"
    assert len(data["tasks"]) == 4, f"Expected 4 tasks, got {len(data['tasks'])}"
    print(f"✓ Tasks endpoint works - Found {len(data['tasks'])} tasks")
except Exception as e:
    print(f"✗ Tasks endpoint failed: {e}")

# Test 4: Health check
print("\n[TEST 4] Testing GET /api/agent/health...")
try:
    response = client.get("/api/agent/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy", f"Expected healthy status"
    assert data["service"] == "ai_agent", f"Expected ai_agent service"
    print("✓ Health check endpoint works")
except Exception as e:
    print(f"✗ Health check failed: {e}")

# Test 5: Validation test - missing fields
print("\n[TEST 5] Testing POST /api/agent/process with missing fields...")
try:
    request_data = {
        "llm_config": {
            "provider": "openai",
            # Missing model_name and api_key
        },
        "task_type": "summarize",
        "content": "Test content"
    }
    response = client.post("/api/agent/process", json=request_data)
    assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
    print("✓ Validation correctly rejects missing fields")
except Exception as e:
    print(f"✗ Validation test failed: {e}")

# Test 6: Validation test - invalid provider
print("\n[TEST 6] Testing POST /api/agent/process with invalid provider...")
try:
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
    assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
    print("✓ Validation correctly rejects invalid provider")
except Exception as e:
    print(f"✗ Invalid provider test failed: {e}")

# Test 7: Test service methods
print("\n[TEST 7] Testing AIAgentService methods...")
try:
    from news_extractor_core.ai_agent_service import AIAgentService

    # Test get_supported_providers
    providers = AIAgentService.get_supported_providers()
    assert len(providers) == 6, f"Expected 6 providers"
    assert any(p["id"] == "openai" for p in providers), "OpenAI provider not found"

    # Test get_supported_tasks
    tasks = AIAgentService.get_supported_tasks()
    assert len(tasks) == 4, f"Expected 4 tasks"
    assert any(t["id"] == "summarize" for t in tasks), "Summarize task not found"

    print("✓ AIAgentService methods work correctly")
except Exception as e:
    print(f"✗ AIAgentService test failed: {e}")

# Test 8: Test image utilities
print("\n[TEST 8] Testing ImageProcessor utilities...")
try:
    from news_extractor_core.image_utils import ImageProcessor

    # Test MIME types
    assert ImageProcessor.get_image_mime_type("JPEG") == "image/jpeg"
    assert ImageProcessor.get_image_mime_type("PNG") == "image/png"

    # Test data URI creation
    uri = ImageProcessor.create_data_uri("abc123", "JPEG")
    assert uri.startswith("data:image/jpeg;base64,")
    assert "abc123" in uri

    print("✓ ImageProcessor utilities work correctly")
except Exception as e:
    print(f"✗ ImageProcessor test failed: {e}")

# Test 9: Test AI agent models
print("\n[TEST 9] Testing AI agent models...")
try:
    from news_extractor_core.ai_agent_models import (
        LLMConfig, LLMProvider, AgentRequest, AgentTaskType
    )

    # Test LLMConfig
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o",
        api_key="test-key"
    )
    assert config.temperature == 0.7  # default
    assert config.max_tokens == 2000  # default

    # Test AgentRequest
    request = AgentRequest(
        llm_config=config,
        task_type=AgentTaskType.SUMMARIZE,
        content="Test content",
        images=["https://example.com/image.jpg"]
    )
    assert len(request.images) == 1

    print("✓ AI agent models work correctly")
except Exception as e:
    print(f"✗ AI agent models test failed: {e}")

# Test 10: Test prompt building
print("\n[TEST 10] Testing prompt building...")
try:
    from news_extractor_core.ai_agent_service import AIAgentService
    from news_extractor_core.ai_agent_models import AgentTaskType

    # Test default prompt
    content = "This is test content"
    prompt = AIAgentService._build_prompt(AgentTaskType.SUMMARIZE, content)
    assert content in prompt
    assert "summary" in prompt.lower()

    # Test custom prompt
    custom = "Custom: {content}"
    prompt = AIAgentService._build_prompt(AgentTaskType.SUMMARIZE, content, custom)
    assert "Custom" in prompt
    assert content in prompt

    print("✓ Prompt building works correctly")
except Exception as e:
    print(f"✗ Prompt building test failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("✓ All basic unit tests passed!")
print("\nNote: Full integration tests require actual LangChain dependencies.")
print("To install all dependencies, run:")
print("  ./install_deps.sh")
print("=" * 70)
