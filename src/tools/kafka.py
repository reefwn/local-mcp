import json

from src.tools import config, kafka_client as kf, mcp


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
async def kafka_consume(topic: str, count: int = 10, timeout_ms: int = 5000) -> str:
    """Consume messages from a Kafka topic (earliest offset, up to `count` messages)."""
    messages = await kf.consume(topic, count, timeout_ms)
    return json.dumps(messages, default=str, indent=2) if messages else "No messages found."
