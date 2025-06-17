"""Essential test fixtures for minimalist tests."""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_notion_client():
    """Mock Notion client for database operations."""
    mock_client = Mock()
    mock_client.pages.create.return_value = {"id": "test-page-id"}
    return mock_client


@pytest.fixture
def mock_health_db(mock_notion_client):
    """Mock health database operations."""
    with patch('db.health_db.get_client', return_value=mock_notion_client):
        yield mock_notion_client


@pytest.fixture
def mock_knowledge_db(mock_notion_client):
    """Mock knowledge database operations."""
    with patch('db.knowledge_db.get_client', return_value=mock_notion_client):
        yield mock_notion_client


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls with configurable responses."""
    mock_choice = Mock()
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    # Patch OpenAI in all modules that use it
    from contextlib import ExitStack
    
    with ExitStack() as stack:
        # Apply patches to all modules
        mock_intent = stack.enter_context(patch('ai.intent.OpenAI'))
        mock_health = stack.enter_context(patch('db.health_db.OpenAI'))
        mock_knowledge = stack.enter_context(patch('db.knowledge_db.OpenAI'))
        
        # All patched classes return the same mock client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_intent.return_value = mock_client
        mock_health.return_value = mock_client  
        mock_knowledge.return_value = mock_client
        
        # Helper method to set response easily
        def set_response(response_data):
            mock_choice.message.content = response_data
        
        mock_client.set_response = set_response
        yield mock_client


@pytest.fixture
def mock_print():
    """Mock print function to capture output."""
    with patch('builtins.print') as mock:
        yield mock


def run_cli_test(text, mock_print, expected_success_message=None):
    """Shared CLI test logic.
    
    Args:
        text: Input text to process
        mock_print: Mocked print function
        expected_success_message: Expected success message substring
    """
    from ingest.cli import handle_log_command
    
    handle_log_command(text)
    
    # Verify success message
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    success_messages = [msg for msg in print_calls if "✅ Saved to" in msg]
    assert len(success_messages) == 1
    
    if expected_success_message:
        assert expected_success_message in success_messages[0]
    
    return success_messages[0]