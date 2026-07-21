from src.config import Config

config = Config()

# Initialize clients only when enabled
jira_cloud_client = None
bitbucket_client = None
obsidian_client = None

# Per-environment client registries: {"dev": Client, "qa": Client, "uat": Client, "prod": Client}
redis_clients: dict[str, "RedisClient"] = {}
kafka_clients: dict[str, "KafkaClient"] = {}
elasticsearch_clients: dict[str, "ElasticsearchClient"] = {}

# Per-(host, environment) PostgreSQL client registry, e.g. {("microservices", "dev"): Client, ...}
# Hosts are open-ended — discovered from whichever POSTGRES_URL_<HOST>_<ENV> vars are set.
postgres_clients: dict[tuple[str, str], "PostgresClient"] = {}

if config.enable_jira or config.enable_confluence:
    from src.clients.atlassian import JiraCloudClient

    jira_cloud_client = JiraCloudClient(config)

if config.enable_bitbucket:
    from src.clients.atlassian import BitbucketClient

    bitbucket_client = BitbucketClient(config)

if config.enable_postgres:
    from src.clients.postgres import PostgresClient

    for _host, _env_urls in config.postgres_host_urls.items():
        for _env, _url in _env_urls.items():
            if _url:
                postgres_clients[(_host, _env)] = PostgresClient(_url)

if config.enable_redis:
    from src.clients.redis import RedisClient

    for _env, _url in config.redis_urls.items():
        if _url:
            redis_clients[_env] = RedisClient(_url)

if config.enable_kafka:
    from src.clients.kafka import KafkaClient

    for _env, _servers in config.kafka_bootstrap_servers.items():
        if _servers:
            kafka_clients[_env] = KafkaClient(
                _servers,
                ssl_enabled=config.kafka_ssl_enabled.get(_env, False),
            )

if config.enable_obsidian:
    from src.clients.obsidian import ObsidianClient
    obsidian_client = ObsidianClient(api_key=config.obsidian_api_key, base_url=config.obsidian_url)

if config.enable_elasticsearch:
    from src.clients.elasticsearch import ElasticsearchClient

    for _env, _url in config.elasticsearch_urls.items():
        if _url:
            elasticsearch_clients[_env] = ElasticsearchClient(
                url=_url,
                api_key=config.elasticsearch_api_keys.get(_env, ""),
                username=config.elasticsearch_usernames.get(_env, ""),
                password=config.elasticsearch_passwords.get(_env, ""),
            )


def resolve_client(clients: dict, environment: str, tool_prefix: str):
    """Look up a per-environment client, raising a clear error if not configured."""
    client = clients.get(environment)
    if client is None:
        available = ", ".join(sorted(clients.keys())) or "none"
        raise ValueError(
            f"No {tool_prefix} client configured for environment '{environment}'. "
            f"Available environments: {available}."
        )
    return client


def resolve_postgres_client(host: str, environment: str) -> "PostgresClient":
    """Look up a PostgreSQL client by (host, environment), raising a clear error if not configured."""
    client = postgres_clients.get((host, environment))
    if client is None:
        available = ", ".join(
            f"{h}/{e}" for h, e in sorted(postgres_clients.keys())
        ) or "none"
        raise ValueError(
            f"No postgres client configured for host '{host}' and environment '{environment}'. "
            f"Available host/environment combos: {available}."
        )
    return client
