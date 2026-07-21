import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import load_tool_functions

_tools = load_tool_functions("src.tools.kafka")
kafka_list_topics = _tools["kafka_list_topics"]
kafka_describe_topic = _tools["kafka_describe_topic"]
kafka_consume = _tools["kafka_consume"]


@pytest.mark.asyncio
async def test_kafka_list_topics_with_results():
    mock_kf = AsyncMock()
    mock_kf.list_topics.return_value = ["b", "a", "c"]
    with patch("src.tools.kafka.kafka_clients", {"uat": mock_kf}):
        result = await kafka_list_topics(environment="uat")
    assert '"a"' in result  # sorted


@pytest.mark.asyncio
async def test_kafka_list_topics_no_results():
    mock_kf = AsyncMock()
    mock_kf.list_topics.return_value = []
    with patch("src.tools.kafka.kafka_clients", {"uat": mock_kf}):
        result = await kafka_list_topics(environment="uat")
    assert result == "No topics found."


@pytest.mark.asyncio
async def test_kafka_describe_topic():
    mock_kf = AsyncMock()
    mock_kf.describe_topic.return_value = [{"topic": "t", "partitions": 3}]
    with patch("src.tools.kafka.kafka_clients", {"uat": mock_kf}):
        result = await kafka_describe_topic("t", environment="uat")
    assert '"topic": "t"' in result



@pytest.mark.asyncio
async def test_kafka_consume_with_messages():
    mock_kf = AsyncMock()
    mock_kf.consume.return_value = [{"topic": "t", "partition": 0, "offset": 0, "key": None, "value": "msg", "timestamp": 123}]
    with patch("src.tools.kafka.kafka_clients", {"uat": mock_kf}):
        result = await kafka_consume("t", environment="uat", count=5, timeout_ms=1000)
    assert '"value": "msg"' in result


@pytest.mark.asyncio
async def test_kafka_consume_no_messages():
    mock_kf = AsyncMock()
    mock_kf.consume.return_value = []
    with patch("src.tools.kafka.kafka_clients", {"uat": mock_kf}):
        result = await kafka_consume("t", environment="uat")
    assert result == "No messages found."


@pytest.mark.asyncio
async def test_kafka_unknown_environment():
    with patch("src.tools.kafka.kafka_clients", {}):
        with pytest.raises(ValueError, match="No kafka client configured for environment 'dev'"):
            await kafka_list_topics(environment="dev")
