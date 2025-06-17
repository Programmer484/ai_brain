"""Essential minimalist tests for core functionality."""

import pytest
from unittest.mock import Mock, patch
from tests.conftest import run_cli_test


def test_cli_health_entry(mock_health_db, mock_openai, mock_print):
    """Test CLI handling health entries end-to-end."""
    with patch('ingest.cli.classify_database') as mock_db_classify, \
         patch('ingest.cli.get_database_module') as mock_get_module:
        
        mock_db_classify.return_value = "health"
        
        # Mock the database module with create_from_text method
        mock_module = Mock()
        mock_module.create_from_text.return_value = "test_page_id"
        mock_get_module.return_value = mock_module
        
        run_cli_test("Slept 8 hours", mock_print, "health")
        mock_module.create_from_text.assert_called_once_with("Slept 8 hours")


def test_cli_knowledge_entry(mock_knowledge_db, mock_openai, mock_print):
    """Test CLI handling knowledge entries end-to-end."""
    with patch('ingest.cli.classify_database') as mock_db_classify, \
         patch('ingest.cli.get_database_module') as mock_get_module:
        
        mock_db_classify.return_value = "knowledge"
        
        # Mock the database module with create_from_text method
        mock_module = Mock()
        mock_module.create_from_text.return_value = "test_page_id"
        mock_get_module.return_value = mock_module
        
        run_cli_test("Python is useful", mock_print, "knowledge")
        mock_module.create_from_text.assert_called_once_with("Python is useful")


def test_database_classification(mock_openai):
    """Test database classification step."""
    from ai.intent import classify_database
    
    # Test health classification
    mock_openai.set_response("health")
    result = classify_database("Slept 8 hours")
    assert result == "health"
    
    # Test knowledge classification
    mock_openai.set_response("knowledge")
    result = classify_database("Python is a programming language")
    assert result == "knowledge"


def test_cli_error_handling(mock_print):
    """Test CLI handles errors gracefully."""
    with patch('ingest.cli.classify_database', side_effect=Exception("API Error")):
        with pytest.raises(SystemExit) as exc_info:
            from ingest.cli import handle_log_command
            handle_log_command("Test input")
        
        # Verify error message was printed
        error_calls = [call for call in mock_print.call_args_list 
                      if "❌ Error saving entry" in str(call)]
        assert len(error_calls) == 1
        
        # Verify exit code 1
        assert exc_info.value.code == 1 