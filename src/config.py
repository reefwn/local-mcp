import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

ENVIRONMENTS = ["dev", "qa", "uat", "prod"]


def _env_map(prefix: str) -> dict[str, str]:
    """Build a per-environment value map, e.g. POSTGRES_URL_DEV, POSTGRES_URL_QA, ..."""
    return {env: os.getenv(f"{prefix}_{env.upper()}", "") for env in ENVIRONMENTS}


def _env_bool_map(prefix: str) -> dict[str, bool]:
    """Build a per-environment boolean map from suffixed environment variables."""
    return {
        env: os.getenv(f"{prefix}_{env.upper()}", "false").lower() == "true"
        for env in ENVIRONMENTS
    }


def _postgres_host_urls() -> dict[str, dict[str, str]]:
    """
    Discover POSTGRES_URL_<HOST>_<ENV> env vars and build a {host: {environment: url}} map.

    Open-ended: any <HOST> is accepted as long as the var ends with a known
    environment suffix (_DEV, _QA, _UAT, _PROD), so new hosts can be added purely
    via env vars without code changes.
    """
    hosts: dict[str, dict[str, str]] = {}
    prefix = "POSTGRES_URL_"
    for key, value in os.environ.items():
        if not value or not key.startswith(prefix):
            continue
        remainder = key[len(prefix):]
        for env in ENVIRONMENTS:
            suffix = f"_{env.upper()}"
            if remainder.endswith(suffix):
                host = remainder[: -len(suffix)].lower()
                if host:
                    hosts.setdefault(host, {})[env] = value
                break
    return hosts


@dataclass
class Config:
    atlassian_domain: str = os.getenv("ATLASSIAN_DOMAIN", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    confluence_email: str = os.getenv("CONFLUENCE_EMAIL", "")
    confluence_api_token: str = os.getenv("CONFLUENCE_API_TOKEN", "")
    bitbucket_email: str = os.getenv("BITBUCKET_EMAIL", "")
    bitbucket_api_token: str = os.getenv("BITBUCKET_API_TOKEN", "")
    bitbucket_workspace: str = os.getenv("BITBUCKET_WORKSPACE", "")
    enable_jira: bool = os.getenv("ENABLE_JIRA", "false").lower() == "true"
    enable_confluence: bool = os.getenv("ENABLE_CONFLUENCE", "false").lower() == "true"
    enable_bitbucket: bool = os.getenv("ENABLE_BITBUCKET", "false").lower() == "true"

    enable_postgres: bool = os.getenv("ENABLE_POSTGRES", "false").lower() == "true"
    postgres_host_urls: dict[str, dict[str, str]] = field(default_factory=_postgres_host_urls)

    enable_redis: bool = os.getenv("ENABLE_REDIS", "false").lower() == "true"
    redis_urls: dict[str, str] = field(default_factory=lambda: _env_map("REDIS_URL"))

    enable_kafka: bool = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
    kafka_bootstrap_servers: dict[str, str] = field(
        default_factory=lambda: _env_map("KAFKA_BOOTSTRAP_SERVERS")
    )
    kafka_ssl_enabled: dict[str, bool] = field(
        default_factory=lambda: _env_bool_map("KAFKA_SSL_ENABLED")
    )

    enable_figma: bool = os.getenv("ENABLE_FIGMA", "false").lower() == "true"
    figma_api_token: str = os.getenv("FIGMA_API_TOKEN", "")

    enable_obsidian: bool = os.getenv("ENABLE_OBSIDIAN", "false").lower() == "true"
    obsidian_api_key: str = os.getenv("OBSIDIAN_API_KEY", "")
    obsidian_url: str = os.getenv("OBSIDIAN_URL", "https://127.0.0.1:27124")

    enable_elasticsearch: bool = os.getenv("ENABLE_ELASTICSEARCH", "false").lower() == "true"
    elasticsearch_urls: dict[str, str] = field(default_factory=lambda: _env_map("ELASTICSEARCH_URL"))
    elasticsearch_api_keys: dict[str, str] = field(default_factory=lambda: _env_map("ELASTICSEARCH_API_KEY"))
    elasticsearch_usernames: dict[str, str] = field(default_factory=lambda: _env_map("ELASTICSEARCH_USERNAME"))
    elasticsearch_passwords: dict[str, str] = field(default_factory=lambda: _env_map("ELASTICSEARCH_PASSWORD"))

    enable_loki: bool = os.getenv("ENABLE_LOKI", "false").lower() == "true"
    loki_urls: dict[str, str] = field(default_factory=lambda: _env_map("LOKI_URL"))
    loki_tokens: dict[str, str] = field(default_factory=lambda: _env_map("LOKI_TOKEN"))
    loki_usernames: dict[str, str] = field(default_factory=lambda: _env_map("LOKI_USERNAME"))
    loki_passwords: dict[str, str] = field(default_factory=lambda: _env_map("LOKI_PASSWORD"))
    loki_tenant_ids: dict[str, str] = field(default_factory=lambda: _env_map("LOKI_TENANT_ID"))

    enable_tempo: bool = os.getenv("ENABLE_TEMPO", "false").lower() == "true"
    tempo_urls: dict[str, str] = field(default_factory=lambda: _env_map("TEMPO_URL"))
    tempo_tokens: dict[str, str] = field(default_factory=lambda: _env_map("TEMPO_TOKEN"))
    tempo_usernames: dict[str, str] = field(default_factory=lambda: _env_map("TEMPO_USERNAME"))
    tempo_passwords: dict[str, str] = field(default_factory=lambda: _env_map("TEMPO_PASSWORD"))
    tempo_tenant_ids: dict[str, str] = field(default_factory=lambda: _env_map("TEMPO_TENANT_ID"))

    @property
    def jira_base_url(self) -> str:
        return f"https://{self.atlassian_domain}/rest/api/3"

    @property
    def confluence_base_url(self) -> str:
        return f"https://{self.atlassian_domain}/wiki/api/v2"

    @property
    def bitbucket_base_url(self) -> str:
        return "https://api.bitbucket.org/2.0"

    def configured_environments(self, urls: dict[str, str]) -> list[str]:
        """Return environments that have a non-empty URL configured."""
        return [env for env, url in urls.items() if url]
