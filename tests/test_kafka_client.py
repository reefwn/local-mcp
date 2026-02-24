import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.clients.kafka import KafkaClient


@pytest.mark.asyncio
async def test_kafka_client_init():
    client = KafkaClient("localhost:9092")
    assert client._servers == "localhost:9092"
    assert client._admin is None
    assert client._producer is None


@pytest.mark.asyncio
async def test_get_admin_creates_admin():
    mock_admin = AsyncMock()
    with patch("src.clients.kafka.AIOKafkaAdminClient", return_value=mock_admin):
        client = KafkaClient("localhost:9092")
        admin = await client._get_admin()
    assert admin is mock_admin
    mock_admin.start.assert_called_once()


@pytest.mark.asyncio
async def test_get_producer_creates_producer():
    mock_producer = AsyncMock()
    with patch("src.clients.kafka.AIOKafkaProducer", return_value=mock_producer):
        client = KafkaClient("localhost:9092")
        producer = await client._get_producer()
    assert producer is mock_producer
    mock_producer.start.assert_called_once()


@pytest.mark.asyncio
async def test_list_topics():
    client = KafkaClient("localhost:9092")
    client._admin = AsyncMock()
    client._admin.list_topics.return_value = ["t1", "t2"]
    result = await client.list_topics()
    assert result == ["t1", "t2"]


@pytest.mark.asyncio
async def test_describe_topic():
    client = KafkaClient("localhost:9092")
    client._admin = AsyncMock()
    client._admin.describe_topics.return_value = [{"topic": "t"}]
    result = await client.describe_topic("t")
    assert result == [{"topic": "t"}]


@pytest.mark.asyncio
async def test_create_topic():
    client = KafkaClient("localhost:9092")
    client._admin = AsyncMock()
    with patch("src.clients.kafka.NewTopic") as mock_nt:
        await client.create_topic("t", 3, 2)
    mock_nt.assert_called_once_with(name="t", num_partitions=3, replication_factor=2)


@pytest.mark.asyncio
async def test_produce_success():
    client = KafkaClient("localhost:9092")
    mock_record = MagicMock(topic="t", partition=0, offset=1)
    client._producer = AsyncMock()
    client._producer.send_and_wait.return_value = mock_record
    result = await client.produce("t", "msg", "key")
    assert result == {"topic": "t", "partition": 0, "offset": 1}
    client._producer.send_and_wait.assert_called_once_with("t", b"msg", key=b"key")


@pytest.mark.asyncio
async def test_consume_success():
    mock_consumer = AsyncMock()
    mock_record = MagicMock(topic="t", partition=0, offset=0, key=b"k", value=b"v", timestamp=123)
    mock_consumer.getmany.return_value = {MagicMock(): [mock_record]}
    with patch("src.clients.kafka.AIOKafkaConsumer", return_value=mock_consumer):
        client = KafkaClient("localhost:9092")
        result = await client.consume("t", count=5, timeout_ms=1000)
    assert result == [{"topic": "t", "partition": 0, "offset": 0, "key": "k", "value": "v", "timestamp": 123}]
    mock_consumer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_close():
    client = KafkaClient("localhost:9092")
    client._producer = AsyncMock()
    client._admin = AsyncMock()
    await client.close()
    client._producer.stop.assert_called_once()
    client._admin.close.assert_called_once()
