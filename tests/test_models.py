import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.api import QueryRequest, QueryResponse, HealthCheckResponse, SourceMessage


class TestAPIModels:
    """Test cases for API models"""
    
    def test_health_check_response_default(self):
        """Test HealthCheckResponse with default values"""
        response = HealthCheckResponse()
        assert response.status == "ok"
        assert response.version == "1.1"
    
    def test_health_check_response_custom(self):
        """Test HealthCheckResponse with custom values"""
        response = HealthCheckResponse(status="healthy", version="2.0")
        assert response.status == "healthy"
        assert response.version == "2.0"
    
    def test_query_request_valid(self):
        """Test valid QueryRequest"""
        request = QueryRequest(
            user_question="What is Python?",
            telegram_user_id="123",
            telegram_chat_id="456"
        )
        assert request.user_question == "What is Python?"
        assert request.telegram_user_id == "123"
        assert request.telegram_chat_id == "456"
    
    def test_query_request_no_chat_id(self):
        """Test QueryRequest without chat_id"""
        request = QueryRequest(
            user_question="What is Python?",
            telegram_user_id="123"
        )
        assert request.telegram_chat_id is None
    
    def test_query_request_missing_required_field(self):
        """Test QueryRequest with missing required field"""
        with pytest.raises(ValidationError):
            QueryRequest(telegram_user_id="123")
    
    def test_source_message_valid(self):
        """Test valid SourceMessage"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        message = SourceMessage(
            message_id="msg_123",
            sender="John Doe",
            timestamp=timestamp,
            text="Hello world"
        )
        assert message.message_id == "msg_123"
        assert message.sender == "John Doe"
        assert message.timestamp == timestamp
        assert message.text == "Hello world"
    
    def test_query_response_valid(self):
        """Test valid QueryResponse"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        source_message = SourceMessage(
            message_id="msg_123",
            sender="John Doe",
            timestamp=timestamp,
            text="Python is great"
        )
        
        response = QueryResponse(
            answer_text="Python is a programming language",
            source_messages=[source_message],
            status="success"
        )
        
        assert response.answer_text == "Python is a programming language"
        assert len(response.source_messages) == 1
        assert response.status == "success"
        assert response.source_messages[0].sender == "John Doe"
    
    def test_query_response_empty_sources(self):
        """Test QueryResponse with empty source messages"""
        response = QueryResponse(
            answer_text="No relevant information found",
            source_messages=[],
            status="no_results"
        )
        
        assert response.answer_text == "No relevant information found"
        assert len(response.source_messages) == 0
        assert response.status == "no_results"