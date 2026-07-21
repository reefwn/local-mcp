import importlib

import pytest
from mcp.server.fastmcp import FastMCP
from unittest.mock import AsyncMock, MagicMock, patch

from src.config import Config
from src.clients import BitbucketClient, JiraCloudClient


def load_tool_functions(module_name: str) -> dict:
    """Return {tool_name: async_fn} after running register() on a tools module."""
    module = importlib.import_module(module_name)
    mcp = FastMCP("test")
    module.register(mcp)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@pytest.fixture
def mock_config():
    return Config(
        atlassian_domain="test.atlassian.net",
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
        postgres_host_urls={"microservices": {"uat": "postgresql://test:test@localhost/test"}},
        enable_redis=True,
        redis_urls={"dev": "", "qa": "", "uat": "redis://localhost:6379", "prod": ""},
        enable_kafka=True,
        kafka_bootstrap_servers={"dev": "", "qa": "", "uat": "localhost:9092", "prod": ""},
        kafka_ssl_enabled={"dev": False, "qa": False, "uat": False, "prod": False},
        enable_figma=True,
        figma_api_token="test-figma-token",
    )


@pytest.fixture
def mock_jira_cloud_client(mock_config):
    with patch("httpx.AsyncClient"):
        client = JiraCloudClient(mock_config)
        client._jira = AsyncMock()
        client._confluence = client._jira
        return client


@pytest.fixture
def mock_bitbucket_client(mock_config):
    with patch("httpx.AsyncClient"):
        client = BitbucketClient(mock_config)
        client._http = AsyncMock()
        return client
