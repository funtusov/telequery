import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.models.api import QueryRequest, QueryResponse, HealthCheckResponse


@pytest.fixture
def sample_query_request():
    """Sample query request for testing"""
    return QueryRequest(
        user_question="Tell me about Python programming",
        telegram_user_id="123",
        telegram_chat_id=None
    )