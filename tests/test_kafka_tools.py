import pytest
from unittest.mock import AsyncMock, patch
from src.tools.kafka import (
    kafka_list_topics, kafka_describe_topic, kafka_create_topic,
    kafka_produce, kafka_consume,
)


@pytest.mark.asyncio
async def test_kafka_list_topics_with_results():
    mock_kf = AsyncMock()
    mock_kf.list_topics.return_value = ["b", "a", "c"]
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_list_topics()
    assert '"a"' in result  # sorted


@pytest.mark.asyncio
async def test_kafka_list_topics_no_results():
    mock_kf = AsyncMock()
    mock_kf.list_topics.return_value = []
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_list_topics()
    assert result == "No topics found."


@pytest.mark.asyncio
async def test_kafka_describe_topic():
    mock_kf = AsyncMock()
    mock_kf.describe_topic.return_value = [{"topic": "t", "partitions": 3}]
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_describe_topic("t")
    assert '"topic": "t"' in result


@pytest.mark.asyncio
async def test_kafka_create_topic():
    mock_kf = AsyncMock()
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_create_topic("new-topic", num_partitions=3, replication_factor=2)
    assert "new-topic" in result
    mock_kf.create_topic.assert_called_once_with("new-topic", 3, 2)


@pytest.mark.asyncio
async def test_kafka_produce_with_key():
    mock_kf = AsyncMock()
    mock_kf.produce.return_value = {"topic": "t", "partition": 0, "offset": 1}
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_produce("t", "msg", "key1")
    assert '"offset": 1' in result
    mock_kf.produce.assert_called_once_with("t", "msg", "key1")


@pytest.mark.asyncio
async def test_kafka_produce_without_key():
    mock_kf = AsyncMock()
    mock_kf.produce.return_value = {"topic": "t", "partition": 0, "offset": 2}
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_produce("t", "msg")
    mock_kf.produce.assert_called_once_with("t", "msg", None)


@pytest.mark.asyncio
async def test_kafka_consume_with_messages():
    mock_kf = AsyncMock()
    mock_kf.consume.return_value = [{"topic": "t", "partition": 0, "offset": 0, "key": None, "value": "msg", "timestamp": 123}]
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_consume("t", count=5, timeout_ms=1000)
    assert '"value": "msg"' in result


@pytest.mark.asyncio
async def test_kafka_consume_no_messages():
    mock_kf = AsyncMock()
    mock_kf.consume.return_value = []
    with patch("src.tools.kafka.kf", mock_kf):
        result = await kafka_consume("t")
    assert result == "No messages found."
