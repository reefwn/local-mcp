import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    domain: str = os.getenv("ATLASSIAN_DOMAIN", "")
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

    @property
    def jira_base_url(self) -> str:
        return f"https://{self.domain}/rest/api/3"

    @property
    def confluence_base_url(self) -> str:
        return f"https://{self.domain}/wiki/api/v2"

    @property
    def bitbucket_base_url(self) -> str:
        return "https://api.bitbucket.org/2.0"
