import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    email: str = os.getenv("ATLASSIAN_EMAIL", "")
    api_token: str = os.getenv("ATLASSIAN_API_TOKEN", "")
    domain: str = os.getenv("ATLASSIAN_DOMAIN", "")
    bitbucket_workspace: str = os.getenv("BITBUCKET_WORKSPACE", "")

    @property
    def jira_base_url(self) -> str:
        return f"https://{self.domain}/rest/api/3"

    @property
    def confluence_base_url(self) -> str:
        return f"https://{self.domain}/wiki/api/v2"

    @property
    def bitbucket_base_url(self) -> str:
        return "https://api.bitbucket.org/2.0"
