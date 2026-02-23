from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic


class KafkaClient:
    """Async Kafka client using aiokafka."""

    def __init__(self, bootstrap_servers: str):
        self._servers = bootstrap_servers
        self._admin: AIOKafkaAdminClient | None = None
        self._producer: AIOKafkaProducer | None = None

    async def _get_admin(self) -> AIOKafkaAdminClient:
        if self._admin is None:
            self._admin = AIOKafkaAdminClient(bootstrap_servers=self._servers)
            await self._admin.start()
        return self._admin

    async def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            self._producer = AIOKafkaProducer(bootstrap_servers=self._servers)
            await self._producer.start()
        return self._producer

    async def list_topics(self) -> dict:
        admin = await self._get_admin()
        metadata = await admin.describe_cluster()
        # list_topics returns a dict of topic -> TopicMetadata
        admin_client = await self._get_admin()
        topics = await admin_client.list_topics()
        return topics

    async def describe_topic(self, topic: str) -> list[dict]:
        admin = await self._get_admin()
        descriptions = await admin.describe_topics([topic])
        return descriptions

    async def create_topic(self, name: str, num_partitions: int = 1, replication_factor: int = 1) -> None:
        admin = await self._get_admin()
        await admin.create_topics([NewTopic(name=name, num_partitions=num_partitions, replication_factor=replication_factor)])

    async def produce(self, topic: str, value: str, key: str | None = None) -> dict:
        producer = await self._get_producer()
        k = key.encode() if key else None
        record = await producer.send_and_wait(topic, value.encode(), key=k)
        return {"topic": record.topic, "partition": record.partition, "offset": record.offset}

    async def consume(self, topic: str, count: int = 10, timeout_ms: int = 5000, group_id: str | None = None) -> list[dict]:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self._servers,
            group_id=group_id or f"local-mcp-{topic}",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        await consumer.start()
        messages = []
        try:
            batch = await consumer.getmany(timeout_ms=timeout_ms, max_records=count)
            for tp, records in batch.items():
                for r in records:
                    messages.append({
                        "topic": r.topic,
                        "partition": r.partition,
                        "offset": r.offset,
                        "key": r.key.decode() if r.key else None,
                        "value": r.value.decode() if r.value else None,
                        "timestamp": r.timestamp,
                    })
        finally:
            await consumer.stop()
        return messages

    async def close(self):
        if self._producer:
            await self._producer.stop()
        if self._admin:
            await self._admin.close()
