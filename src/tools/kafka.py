import json

from src.clients.kafka import KafkaClient
from src.tools import config, mcp

kf = KafkaClient(config.kafka_bootstrap_servers)


@mcp.tool()
async def kafka_list_topics() -> str:
    """List all Kafka topics."""
    topics = await kf.list_topics()
    return json.dumps(sorted(topics), indent=2) if topics else "No topics found."


@mcp.tool()
async def kafka_describe_topic(topic: str) -> str:
    """Describe a Kafka topic (partitions, replicas, ISR)."""
    descriptions = await kf.describe_topic(topic)
    return json.dumps(descriptions, default=str, indent=2)


@mcp.tool()
async def kafka_create_topic(name: str, num_partitions: int = 1, replication_factor: int = 1) -> str:
    """Create a new Kafka topic."""
    await kf.create_topic(name, num_partitions, replication_factor)
    return f"Topic '{name}' created (partitions={num_partitions}, replication={replication_factor})."


@mcp.tool()
async def kafka_produce(topic: str, value: str, key: str | None = None) -> str:
    """Produce a message to a Kafka topic. Optionally specify a key."""
    record = await kf.produce(topic, value, key)
    return json.dumps(record, indent=2)


@mcp.tool()
async def kafka_consume(topic: str, count: int = 10, timeout_ms: int = 5000) -> str:
    """Consume messages from a Kafka topic (earliest offset, up to `count` messages)."""
    messages = await kf.consume(topic, count, timeout_ms)
    return json.dumps(messages, default=str, indent=2) if messages else "No messages found."
