# Local MCP Server

MCP server for development and debugging tools — Atlassian (Jira, Confluence, Bitbucket), databases (PostgreSQL, Redis), messaging (Kafka), APM/logging (Elasticsearch, Elastic APM), design (Figma), and notes (Obsidian).

## Setup

There are two environment files for the two Docker Compose services:

| File | Service | Port | Purpose |
|------|---------|------|---------|
| `.env.dev` | `dev` | 7373 | Atlassian, Figma, Obsidian |
| `.env.debug` | `debug` | 7374 | PostgreSQL, Redis, Kafka, Elasticsearch/APM |

Copy the example files and fill in your values:

```bash
cp .env.dev.example .env.dev
cp .env.debug.example .env.debug
```

> `.env.example` is still available if you want to run a single instance with all services via `python -m src.server` or standalone Docker.

### Environment variables

   **Atlassian:**

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

   **PostgreSQL:**

   | Variable | How to get it |
   |----------|---------------|
   | `POSTGRES_URL` | Connection string, e.g. `postgresql://user:password@localhost:5432/dbname` |

   **Redis:**

   | Variable | How to get it |
   |----------|---------------|
   | `REDIS_URL` | Connection string, e.g. `redis://localhost:6379/0` |

   **Kafka:**

   | Variable | How to get it |
   |----------|---------------|
   | `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated broker addresses, e.g. `localhost:9092` |

   **Figma:**

   | Variable | How to get it |
   |----------|---------------|
   | `FIGMA_API_TOKEN` | Generate at [Figma Settings → Personal access tokens](https://www.figma.com/developers/api#access-tokens) |

   > Figma tools are designed to work without Dev Mode

   **Obsidian:**

   | Variable | How to get it |
   |----------|---------------|
   | `OBSIDIAN_API_KEY` | Get from Obsidian Local REST API plugin settings |
   | `OBSIDIAN_URL` | Default: `https://127.0.0.1:27124` |

   > Requires [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin installed in Obsidian

   **Elasticsearch:**

   | Variable | How to get it |
   |----------|---------------|
   | `ELASTICSEARCH_URL` | Connection URL, e.g. `http://localhost:9200` |
   | `ELASTICSEARCH_API_KEY` | API key for authentication (optional) |
   | `ELASTICSEARCH_USERNAME` | Username for Basic Auth (optional) |
   | `ELASTICSEARCH_PASSWORD` | Password for Basic Auth (optional) |

   > Use either API key or username/password authentication

   You can also enable individual services by setting feature flags to `true`:

   | Variable | Default |
   |----------|---------|
   | `ENABLE_JIRA` | `false` |
   | `ENABLE_CONFLUENCE` | `false` |
   | `ENABLE_BITBUCKET` | `false` |
   | `ENABLE_POSTGRES` | `false` |
   | `ENABLE_REDIS` | `false` |
   | `ENABLE_KAFKA` | `false` |
   | `ENABLE_FIGMA` | `false` |
   | `ENABLE_OBSIDIAN` | `false` |
   | `ENABLE_ELASTICSEARCH` | `false` |

## Run locally

```bash
pip install -e .
python -m src.server
```

## Run with Docker Compose

```bash
docker compose up -d        # start in background
docker compose down          # stop
docker compose up -d --build # rebuild and start
```

## Run with Docker

```bash
docker build -t local-mcp .
docker run -d --rm --name local-mcp-server --env-file .env -p 7373:7373 local-mcp
```

## Tests

```bash
pip install -e ".[test]"
pytest
```

## Tools

| Tool | Description |
|------|-------------|
| `jira_search` | Search issues with JQL |
| `jira_get_issue` | Get issue details by key (includes custom fields) |
| `jira_create_issue` | Create a new issue |
| `jira_add_comment` | Add a comment to an issue |
| `jira_update_custom_field` | Update a custom field on an issue |
| `confluence_search` | Search pages by title |
| `confluence_get_page` | Get page content by ID |
| `bitbucket_list_repos` | List workspace repositories |
| `bitbucket_list_prs` | List pull requests for a repo |
| `bitbucket_get_pr` | Get PR details |
| `bitbucket_get_pr_diff` | Get the full diff of a pull request |
| `bitbucket_list_pr_comments` | List comments on a pull request |
| `bitbucket_update_pr_description` | Update the description of a PR |
| `bitbucket_create_pr_comment` | Post a comment on a pull request |
| `pg_query` | Run a read-only SQL query (enforced via read-only transaction) |
| `pg_list_tables` | List tables in a schema |
| `pg_describe_table` | Describe columns of a table |
| `pg_list_indexes` | List indexes on a table |
| `redis_get` | Get the value of a Redis key |
| `redis_keys` | List keys matching a glob pattern |
| `kafka_list_topics` | List all Kafka topics |
| `kafka_describe_topic` | Describe a Kafka topic |
| `kafka_consume` | Consume messages from a topic |
| `figma_get_file` | Get a Figma file's structure and metadata |
| `figma_get_file_nodes` | Get specific nodes from a Figma file by IDs |
| `figma_get_images` | Export Figma nodes as images (png, jpg, svg, pdf) |
| `figma_get_comments` | Get all comments on a Figma file |
| `figma_post_comment` | Post or reply to a comment on a Figma file |
| `obsidian_list_files_in_vault` | List all files in vault root |
| `obsidian_list_files_in_dir` | List files in a specific directory |
| `obsidian_get_file_contents` | Get content of a file |
| `obsidian_simple_search` | Simple text search across vault |
| `obsidian_complex_search` | JsonLogic-based search with glob/regexp |
| `obsidian_append_content` | Append content to a file |
| `obsidian_patch_content` | Insert content relative to heading/block/frontmatter |
| `obsidian_put_content` | Create or update file content |
| `obsidian_delete_file` | Delete a file or directory |
| `obsidian_get_periodic_note` | Get current periodic note (daily/weekly/monthly/etc) |
| `obsidian_get_recent_periodic_notes` | Get recent periodic notes |
| `obsidian_get_recent_changes` | Get recently modified files |
| `elasticsearch_search` | Search logs with query string and time range |
| `elasticsearch_aggregate_errors` | Find most common error patterns |
| `elasticsearch_get_document` | Get a specific log document by ID |
| `elasticsearch_list_indices` | List all indices with stats |
| `elasticsearch_trace_request` | Follow a distributed trace by trace ID |
| `apm_search_traces` | Search APM traces by service, type, or duration |
| `apm_get_trace` | Get full trace details with all spans |
| `apm_search_errors` | Search APM errors by service, message, or type |
| `apm_get_error` | Get full error details with stack trace |
| `apm_list_services` | List all services with recent activity |
| `apm_get_service_metrics` | Get service throughput, latency, error rate |
| `apm_find_slow_transactions` | Find transactions exceeding duration threshold |
