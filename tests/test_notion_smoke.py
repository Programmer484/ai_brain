"""Smoke tests for Notion backend functionality.

Uses mocking to simulate Notion client responses and verify that
our backend functions work without requiring real Notion tokens.
"""

from unittest.mock import Mock, patch
from datetime import date, datetime
import pytest

from db import health, knowledge


class TestNotionHealthSmoke:
    """Smoke tests for health.py module."""
    
    @patch('db.health.get_client')
    def test_create_health_record(self, mock_get_client):
        """Test creating a health record returns page ID."""
        # Mock the Notion client
        mock_client = Mock()
        mock_client.pages.create.return_value = {"id": "test-page-id"}
        mock_get_client.return_value = mock_client
        
        # Create a test record
        record = health.HealthRecord(
            date=date(2024, 1, 1),
            metric="weight",
            value=70.5
        )
        
        # Should return page ID without exception
        page_id = health.create(record)
        assert page_id == "test-page-id"
        
        # Verify the client was called with expected parameters
        mock_client.pages.create.assert_called_once()
    
    @patch('db.health.get_client')
    def test_query_health_records(self, mock_get_client):
        """Test querying health records returns results."""
        # Mock the Notion client
        mock_client = Mock()
        mock_client.databases.query.return_value = {"results": [{"id": "page1"}, {"id": "page2"}]}
        mock_get_client.return_value = mock_client
        
        # Should return results without exception
        results = health.query()
        assert len(results) == 2
        assert results[0]["id"] == "page1"
        
        # Verify the client was called
        mock_client.databases.query.assert_called_once()
    
    @patch('db.health.get_client')
    def test_update_health_record(self, mock_get_client):
        """Test updating a health record returns updated data."""
        # Mock the Notion client
        mock_client = Mock()
        mock_client.pages.update.return_value = {"id": "test-page-id", "updated": True}
        mock_get_client.return_value = mock_client
        
        # Should return updated data without exception
        result = health.update("test-page-id", {"Value": {"number": 75.0}})
        assert result["id"] == "test-page-id"
        assert result["updated"] is True
        
        # Verify the client was called
        mock_client.pages.update.assert_called_once()


class TestNotionKnowledgeSmoke:
    """Smoke tests for knowledge.py module."""
    
    @patch('db.knowledge.get_client')
    def test_create_knowledge_record(self, mock_get_client):
        """Test creating a knowledge record returns page ID."""
        # Mock the Notion client
        mock_client = Mock()
        mock_client.pages.create.return_value = {"id": "test-knowledge-id"}
        mock_get_client.return_value = mock_client
        
        # Create a test record
        record = knowledge.KnowledgeRecord(
            text="This is a test knowledge entry",
            created_ts=datetime(2024, 1, 1, 12, 0, 0),
            tags=["test", "example"]
        )
        
        # Should return page ID without exception
        page_id = knowledge.create(record)
        assert page_id == "test-knowledge-id"
        
        # Verify the client was called with expected parameters
        mock_client.pages.create.assert_called_once()
    
    @patch('db.knowledge.get_client')
    def test_query_knowledge_records(self, mock_get_client):
        """Test querying knowledge records returns results."""
        # Mock the Notion client
        mock_client = Mock()
        mock_client.databases.query.return_value = {"results": [{"id": "knowledge1"}]}
        mock_get_client.return_value = mock_client
        
        # Should return results without exception
        results = knowledge.query()
        assert len(results) == 1
        assert results[0]["id"] == "knowledge1"
        
        # Verify the client was called
        mock_client.databases.query.assert_called_once()
    
    @patch('db.knowledge.get_client')
    def test_update_knowledge_record(self, mock_get_client):
        """Test updating a knowledge record returns updated data."""
        # Mock the Notion client
        mock_client = Mock()
        mock_client.pages.update.return_value = {"id": "test-knowledge-id", "updated": True}
        mock_get_client.return_value = mock_client
        
        # Should return updated data without exception
        result = knowledge.update("test-knowledge-id", {"Tags": {"multi_select": [{"name": "updated"}]}})
        assert result["id"] == "test-knowledge-id"
        assert result["updated"] is True
        
        # Verify the client was called
        mock_client.pages.update.assert_called_once() 