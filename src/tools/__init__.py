from mcp.server.fastmcp import FastMCP

from src.config import Config

mcp = FastMCP("local-mcp-server", host="0.0.0.0", port=7373)
config = Config()

# Initialize clients only when enabled
atlassian_client = None
postgres_client = None
redis_client = None
kafka_client = None
obsidian_client = None
elasticsearch_client = None

if config.enable_jira or config.enable_confluence or config.enable_bitbucket:
    from src.clients.atlassian import AtlassianClient
    atlassian_client = AtlassianClient(config)

if config.enable_postgres:
    from src.clients.postgres import PostgresClient
    postgres_client = PostgresClient(config.postgres_url)

if config.enable_redis:
    from src.clients.redis import RedisClient
    redis_client = RedisClient(config.redis_url)

if config.enable_kafka:
    from src.clients.kafka import KafkaClient
    kafka_client = KafkaClient(config.kafka_bootstrap_servers, ssl_enabled=config.kafka_ssl_enabled)

if config.enable_obsidian:
    from src.clients.obsidian import ObsidianClient
    obsidian_client = ObsidianClient(api_key=config.obsidian_api_key, base_url=config.obsidian_url)

if config.enable_elasticsearch:
    from src.clients.elasticsearch import ElasticsearchClient
    elasticsearch_client = ElasticsearchClient(
        url=config.elasticsearch_url,
        api_key=config.elasticsearch_api_key,
        username=config.elasticsearch_username,
        password=config.elasticsearch_password
    )
