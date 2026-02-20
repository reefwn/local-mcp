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
   | `ATLASSIAN_DOMAIN` | Your domain from the browser URL, e.g. `your-company.atlassian.net` |
   | `JIRA_EMAIL` | Email for Jira access |
   | `JIRA_API_TOKEN` | Generate at [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens) |
   | `CONFLUENCE_EMAIL` | Email for Confluence access |
   | `CONFLUENCE_API_TOKEN` | Generate at [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens) |
   | `BITBUCKET_EMAIL` | Email for Bitbucket access |
   | `BITBUCKET_API_TOKEN` | Generate at [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens) |
   | `BITBUCKET_WORKSPACE` | Your workspace slug from the URL `https://bitbucket.org/{workspace-slug}/`, or find it under Workspace Settings → "Workspace ID" |

   > Each service uses its own API token via Basic Auth (email + token). You can use the same token for all three, or create separate tokens with scoped permissions.

   You can also disable individual services by setting feature flags to `false`:

   | Variable | Default |
   |----------|---------|
   | `ENABLE_JIRA` | `false` |
   | `ENABLE_CONFLUENCE` | `false` |
   | `ENABLE_BITBUCKET` | `false` |

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
