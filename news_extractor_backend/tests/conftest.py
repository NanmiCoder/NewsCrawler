# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures
"""
import sys
from unittest.mock import Mock, MagicMock

# Mock langchain modules before any imports
langchain_mock = MagicMock()
langchain_core_mock = MagicMock()
langchain_core_messages_mock = MagicMock()
langchain_core_language_models_mock = MagicMock()
langchain_openai_mock = MagicMock()
langchain_anthropic_mock = MagicMock()
langchain_google_genai_mock = MagicMock()

sys.modules['langchain'] = langchain_mock
sys.modules['langchain_core'] = langchain_core_mock
sys.modules['langchain_core.messages'] = langchain_core_messages_mock
sys.modules['langchain_core.language_models'] = langchain_core_language_models_mock
sys.modules['langchain_openai'] = langchain_openai_mock
sys.modules['langchain_anthropic'] = langchain_anthropic_mock
sys.modules['langchain_google_genai'] = langchain_google_genai_mock

# Create mock classes
class MockHumanMessage:
    def __init__(self, content):
        self.content = content

class MockSystemMessage:
    def __init__(self, content):
        self.content = content

class MockChatModel:
    async def ainvoke(self, messages):
        response = Mock()
        response.content = "Mocked AI response"
        return response

# Assign mocks
langchain_core_messages_mock.HumanMessage = MockHumanMessage
langchain_core_messages_mock.SystemMessage = MockSystemMessage
langchain_core_language_models_mock.BaseChatModel = MockChatModel
