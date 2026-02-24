from src.config import Config


def test_config_defaults():
    config = Config(domain="", jira_email="", enable_jira=False, enable_postgres=False)
    assert config.domain == ""
    assert config.jira_email == ""
    assert config.enable_jira is False
    assert config.enable_postgres is False


def test_config_properties():
    config = Config(domain="test.atlassian.net")
    assert config.jira_base_url == "https://test.atlassian.net/rest/api/3"
    assert config.confluence_base_url == "https://test.atlassian.net/wiki/api/v2"
    assert config.bitbucket_base_url == "https://api.bitbucket.org/2.0"
