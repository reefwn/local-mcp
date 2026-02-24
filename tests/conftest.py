import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.config import Config
from src.clients import AtlassianClient


@pytest.fixture
def mock_config():
    return Config(
        domain="test.atlassian.net",
        jira_email="test@example.com",
        jira_api_token="test-token",
        confluence_email="test@example.com",
        confluence_api_token="test-token",
        bitbucket_email="test@example.com",
        bitbucket_api_token="test-token",
        bitbucket_workspace="test-workspace",
        enable_jira=True,
        enable_confluence=True,
        enable_bitbucket=True,
        enable_postgres=True,
        postgres_url="postgresql://test:test@localhost/test",
        enable_redis=True,
        redis_url="redis://localhost:6379",
        enable_kafka=True,
        kafka_bootstrap_servers="localhost:9092",
        enable_figma=True,
        figma_api_token="test-figma-token",
    )


@pytest.fixture
def mock_atlassian_client(mock_config):
    with patch("httpx.AsyncClient"):
        client = AtlassianClient(mock_config)
        client._jira = AsyncMock()
        client._confluence = AsyncMock()
        client._bitbucket = AsyncMock()
        return client
