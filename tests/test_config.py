import os

from src.config import Config


def test_config_defaults():
    config = Config(
        atlassian_domain="",
        jira_email="",
        enable_jira=False,
        enable_postgres=False,
        kafka_ssl_enabled={"dev": False, "qa": False, "uat": False, "prod": False},
    )
    assert config.atlassian_domain == ""
    assert config.jira_email == ""
    assert config.enable_jira is False
    assert config.enable_postgres is False
    assert config.kafka_ssl_enabled["dev"] is False


def test_config_properties():
    config = Config(atlassian_domain="test.atlassian.net")
    assert config.jira_base_url == "https://test.atlassian.net/rest/api/3"
    assert config.confluence_base_url == "https://test.atlassian.net/wiki/api/v2"
    assert config.bitbucket_base_url == "https://api.bitbucket.org/2.0"


def test_config_per_environment_urls():
    config = Config(
        redis_urls={"dev": "redis://dev", "qa": "", "uat": "redis://uat", "prod": ""},
    )
    assert config.configured_environments(config.redis_urls) == ["dev", "uat"]


def test_config_per_environment_kafka(monkeypatch):
    for key in list(os.environ):
        if key.startswith("KAFKA_BOOTSTRAP_SERVERS_") or key.startswith("KAFKA_SSL_ENABLED_"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS_DEV", "dev-kafka:9092")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS_UAT", "uat-kafka:9093")
    monkeypatch.setenv("KAFKA_SSL_ENABLED_UAT", "true")

    config = Config()

    assert config.kafka_bootstrap_servers == {
        "dev": "dev-kafka:9092",
        "qa": "",
        "uat": "uat-kafka:9093",
        "prod": "",
    }
    assert config.kafka_ssl_enabled == {
        "dev": False,
        "qa": False,
        "uat": True,
        "prod": False,
    }


def test_config_postgres_host_urls_discovery(monkeypatch):
    # Isolate from any real POSTGRES_URL_* vars loaded from a local .env file.
    for key in list(os.environ):
        if key.startswith("POSTGRES_URL_"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("POSTGRES_URL_MICROSERVICES_DEV", "postgresql://dev-microservices")
    monkeypatch.setenv("POSTGRES_URL_MICROSERVICES_UAT", "postgresql://uat-microservices")
    monkeypatch.setenv("POSTGRES_URL_MERCHANT_QA", "postgresql://qa-merchant")

    config = Config()

    assert config.postgres_host_urls["microservices"] == {
        "dev": "postgresql://dev-microservices",
        "uat": "postgresql://uat-microservices",
    }
    assert config.postgres_host_urls["merchant"] == {"qa": "postgresql://qa-merchant"}
    assert "openapipartner" not in config.postgres_host_urls
