# Local MCP Server

Aggregated MCP server for Atlassian tools — Jira, Confluence, and Bitbucket — running in a single Docker container.

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your `.env` values:

   | Variable | How to get it |
   |----------|---------------|
   | `ATLASSIAN_EMAIL` | The email you use to log into Atlassian |
   | `ATLASSIAN_DOMAIN` | Your domain from the browser URL, e.g. `your-company.atlassian.net` |
   | `ATLASSIAN_API_TOKEN` | Generate at [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens) — click "Create API token", give it a label, and copy the value |
   | `BITBUCKET_WORKSPACE` | Your workspace slug from the URL `https://bitbucket.org/{workspace-slug}/`, or find it under Workspace Settings → "Workspace ID" |

   > The API token uses Basic Auth (email + token) and works for Jira, Confluence, and Bitbucket Cloud under the same Atlassian account.

## Run locally

```bash
pip install -e .
python -m src.server
```

## Run with Docker

```bash
docker build -t local-mcp .
docker run -i --env-file .env local-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `jira_search` | Search issues with JQL |
| `jira_get_issue` | Get issue details by key |
| `jira_create_issue` | Create a new issue |
| `confluence_search` | Search pages by title |
| `confluence_get_page` | Get page content by ID |
| `bitbucket_list_repos` | List workspace repositories |
| `bitbucket_list_prs` | List pull requests for a repo |
| `bitbucket_get_pr` | Get PR details |
