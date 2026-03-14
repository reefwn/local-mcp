import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


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
    postgres_url: str = os.getenv("POSTGRES_URL", "")
    enable_redis: bool = os.getenv("ENABLE_REDIS", "false").lower() == "true"
    redis_url: str = os.getenv("REDIS_URL", "")
    enable_kafka: bool = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
    enable_figma: bool = os.getenv("ENABLE_FIGMA", "false").lower() == "true"
    figma_api_token: str = os.getenv("FIGMA_API_TOKEN", "")
    enable_obsidian: bool = os.getenv("ENABLE_OBSIDIAN", "false").lower() == "true"
    obsidian_api_key: str = os.getenv("OBSIDIAN_API_KEY", "")
    obsidian_url: str = os.getenv("OBSIDIAN_URL", "https://127.0.0.1:27124")
    enable_elasticsearch: bool = os.getenv("ENABLE_ELASTICSEARCH", "false").lower() == "true"
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    elasticsearch_api_key: str = os.getenv("ELASTICSEARCH_API_KEY", "")
    elasticsearch_username: str = os.getenv("ELASTICSEARCH_USERNAME", "")
    elasticsearch_password: str = os.getenv("ELASTICSEARCH_PASSWORD", "")

    @property
    def jira_base_url(self) -> str:
        return f"https://{self.atlassian_domain}/rest/api/3"

    @property
    def confluence_base_url(self) -> str:
        return f"https://{self.atlassian_domain}/wiki/api/v2"

    @property
    def bitbucket_base_url(self) -> str:
        return "https://api.bitbucket.org/2.0"
