import json

from mcp.server.fastmcp import FastMCP

from src.tools import kafka_clients, resolve_client


def _client(environment: str):
    return resolve_client(kafka_clients, environment, "kafka")


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def kafka_list_topics(environment: str) -> str:
        """List all Kafka topics.

        Args:
            environment: Target environment (dev, qa, uat, prod).
        """
        topics = await _client(environment).list_topics()
        return json.dumps(sorted(topics), indent=2) if topics else "No topics found."

    @mcp.tool()
    async def kafka_describe_topic(topic: str, environment: str) -> str:
        """Describe a Kafka topic (partitions, replicas, ISR).

        Args:
            topic: Kafka topic to describe.
            environment: Target environment (dev, qa, uat, prod).
        """
        descriptions = await _client(environment).describe_topic(topic)
        return json.dumps(descriptions, default=str, indent=2)

    @mcp.tool()
    async def kafka_consume(
        topic: str, environment: str, count: int = 10, timeout_ms: int = 5000
    ) -> str:
        """Consume messages from a Kafka topic (earliest offset, up to `count` messages).

        Args:
            topic: Kafka topic to consume.
            environment: Target environment (dev, qa, uat, prod).
            count: Maximum number of messages to consume.
            timeout_ms: Maximum time to wait for messages in milliseconds.
        """
        messages = await _client(environment).consume(topic, count, timeout_ms)
        return json.dumps(messages, default=str, indent=2) if messages else "No messages found."
