# Local MCP Server

MCP server for development and debugging tools — Atlassian (Jira, Confluence, Bitbucket), databases (PostgreSQL, Redis), messaging (Kafka), observability (Elasticsearch, Elastic APM, Loki, Tempo), design (Figma), and notes (Obsidian).

Each client group runs on its own port within a single container, so your agent can connect to individual clients independently.

## Architecture

One container, multiple MCP servers running concurrently — one per client group, each on its own port:

| Port | Client | Tools |
|------|--------|-------|
| 7373 | Atlassian | Jira, Confluence, Bitbucket |
| 7374 | PostgreSQL | pg_query, pg_list_tables, pg_describe_table, pg_list_indexes |
| 7375 | Redis | redis_get, redis_keys |
| 7376 | Kafka | kafka_list_topics, kafka_describe_topic, kafka_consume |
| 7377 | Figma | figma_get_file, figma_get_file_nodes, figma_get_images, figma_get_comments, figma_post_comment |
| 7378 | Obsidian | obsidian_* |
| 7379 | Elasticsearch + APM | elasticsearch_*, apm_* |
| 7380 | Loki | loki_* |
| 7381 | Tempo | tempo_* |

Only ports for enabled clients are actually bound. Disabled clients don't start a server.

## Setup

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

### Environment variables

**Feature flags** — enable only the clients you need:

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
| `ENABLE_LOKI` | `false` |
| `ENABLE_TEMPO` | `false` |

**Atlassian Cloud** (Jira + Confluence — one client, same site domain):

| Variable | How to get it |
|----------|---------------|
| `ATLASSIAN_DOMAIN` | Your domain from the browser URL, e.g. `your-company.atlassian.net` |
| `JIRA_EMAIL` | Email for Jira/Confluence access |
| `JIRA_API_TOKEN` | Generate at [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `CONFLUENCE_EMAIL` | Optional override; defaults to `JIRA_EMAIL` |
| `CONFLUENCE_API_TOKEN` | Optional override; defaults to `JIRA_API_TOKEN` |

**Bitbucket** (separate client and credentials):

| Variable | How to get it |
|----------|---------------|
| `BITBUCKET_EMAIL` | Email for Bitbucket access |
| `BITBUCKET_API_TOKEN` | Generate at [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `BITBUCKET_WORKSPACE` | Your workspace slug from `https://bitbucket.org/{workspace-slug}/` |

> Jira and Confluence typically share one Atlassian Cloud API token. Bitbucket uses its own credentials and is only initialized when `ENABLE_BITBUCKET=true`.

**PostgreSQL supports multiple named hosts, each with its own credentials** (e.g. `microservices`, `merchant`, `openapipartner`), each available per environment (`dev`, `qa`, `uat`, `prod`) — see [PostgreSQL: multi-host support](#postgresql-multi-host-support) below.

**Redis, Kafka, Elasticsearch, Loki, and Tempo tools support multiple environments** (`dev`, `qa`, `uat`, `prod`) selectable per call via an `environment` parameter — see [Multi-environment support](#multi-environment-support) below.

**Figma:**

| Variable | How to get it |
|----------|---------------|
| `FIGMA_API_TOKEN` | Generate at [Figma Settings → Personal access tokens](https://www.figma.com/developers/api#access-tokens) |

> Figma tools work without Dev Mode.

**Obsidian:**

| Variable | How to get it |
|----------|---------------|
| `OBSIDIAN_API_KEY` | Get from Obsidian Local REST API plugin settings |
| `OBSIDIAN_URL` | Default: `https://127.0.0.1:27124` |

> Requires the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin.

**Elasticsearch / APM:** configured per environment — see [Multi-environment support](#multi-environment-support).

**Loki / Tempo:** configured per environment. Their tools default to `environment="all"` and merge results from every configured environment for incident debugging.

## PostgreSQL: multi-host support

PostgreSQL is modeled as a set of independently credentialed **hosts** (e.g. `microservices`, `merchant`, `openapipartner`), each available per **environment** (`dev`, `qa`, `uat`, `prod`). Every `pg_*` tool call requires `host` and `environment`; the MCP server resolves the matching connection string server-side using `POSTGRES_URL_<HOST>_<ENV>` env vars — **credentials never leave the MCP server or get exposed to the calling agent.**

Hosts are open-ended: adding a new host is just setting new `POSTGRES_URL_<NEWHOST>_<ENV>` vars — no code changes needed. Only host/environment combos with a non-empty URL are available; calling `pg_*` with an unconfigured combo returns a clear error listing which combos exist.

| Variable pattern | Example |
|-------------------|---------|
| `POSTGRES_URL_<HOST>_DEV` | `POSTGRES_URL_MICROSERVICES_DEV=postgresql://user:password@microservices-dev-host:5432/dbname` |
| `POSTGRES_URL_<HOST>_QA` | `POSTGRES_URL_MERCHANT_QA=postgresql://user:password@merchant-qa-host:5432/dbname` |
| `POSTGRES_URL_<HOST>_UAT` | `POSTGRES_URL_OPENAPIPARTNER_UAT=postgresql://user:password@openapipartner-uat-host:5432/dbname` |
| `POSTGRES_URL_<HOST>_PROD` | `POSTGRES_URL_MICROSERVICES_PROD=postgresql://user:password@microservices-prod-host:5432/dbname` |

The optional `db` parameter on `pg_*` tools still lets the agent switch databases within the same host (default: the database from that host's connection URL).

Example tool call:

```json
{ "tool": "pg_query", "arguments": { "sql": "SELECT 1", "host": "microservices", "environment": "dev" } }
```

## Multi-environment support

`redis_*`, `kafka_*`, `elasticsearch_*`, and `apm_*` tools require an explicit environment. Loki and Tempo accept the same environment names and additionally default to `all`, which queries every configured backend concurrently and merges results. A failed environment is reported in the response without hiding successful results from other environments.

Configure connection settings per environment using suffixed variables. Only environments with a non-empty URL or bootstrap-server value are available; calling a tool with an unconfigured `environment` returns a clear error listing which environments are available.

**Redis:**

| Variable | Example |
|----------|---------|
| `REDIS_URL_DEV` | `redis://dev-host:6379/0` |
| `REDIS_URL_QA` | `redis://qa-host:6379/0` |
| `REDIS_URL_UAT` | `redis://uat-host:6379/0` |
| `REDIS_URL_PROD` | `redis://prod-host:6379/0` |

**Kafka:**

| Variable | Example |
|----------|---------|
| `KAFKA_BOOTSTRAP_SERVERS_<ENV>` | `uat-kafka-host:9093` |
| `KAFKA_SSL_ENABLED_<ENV>` | `true` (defaults to `false`) |

**Elasticsearch / APM:** (repeat suffix pattern per environment: `_DEV`, `_QA`, `_UAT`, `_PROD`)

| Variable | How to get it |
|----------|---------------|
| `ELASTICSEARCH_URL_<ENV>` | e.g. `http://uat-host:9200` |
| `ELASTICSEARCH_API_KEY_<ENV>` | API key (optional) |
| `ELASTICSEARCH_USERNAME_<ENV>` | Username for Basic Auth (optional) |
| `ELASTICSEARCH_PASSWORD_<ENV>` | Password for Basic Auth (optional) |

> Use either API key or username/password per environment, not both.

**Loki / Tempo:** (repeat suffix pattern per environment: `_DEV`, `_QA`, `_UAT`, `_PROD`)

| Variable | Description |
|----------|-------------|
| `LOKI_URL_<ENV>` | Loki query endpoint, e.g. `http://loki:3100` |
| `TEMPO_URL_<ENV>` | Tempo query endpoint, e.g. `http://tempo:3200` |
| `LOKI_TOKEN_<ENV>` / `TEMPO_TOKEN_<ENV>` | Optional Bearer token |
| `LOKI_USERNAME_<ENV>` / `TEMPO_USERNAME_<ENV>` | Optional Basic Auth username |
| `LOKI_PASSWORD_<ENV>` / `TEMPO_PASSWORD_<ENV>` | Optional Basic Auth password |
| `LOKI_TENANT_ID_<ENV>` / `TEMPO_TENANT_ID_<ENV>` | Optional multi-tenant `X-Scope-OrgID` |

Use either a token or username/password for a backend. A token takes precedence when both are set.

Aggregated Loki example:

```json
{ "tool": "loki_search_logs", "arguments": { "query": "{service_name=\"checkout\"} |= \"error\"", "hours_ago": 2, "limit": 100 } }
```

Aggregated Tempo example:

```json
{ "tool": "tempo_search_traces", "arguments": { "query": "{ status = error }", "hours_ago": 2, "limit": 20 } }
```

Example tool call targeting dev explicitly:

```json
{ "tool": "elasticsearch_search", "arguments": { "index": "logs-*", "query": "error", "environment": "dev" } }
```

Kafka calls use the same explicit selection:

```json
{ "tool": "kafka_list_topics", "arguments": { "environment": "uat" } }
```

## Run locally

```bash
pip install -e .
python -m src.server
```

## Run with Docker Compose

```bash
docker compose up -d         # start in background
docker compose down          # stop
docker compose up -d --build # rebuild and start
```

## Run with Docker

```bash
docker build -t local-mcp .
docker run -d --rm --name local-mcp --env-file .env \
  -p 7373:7373 -p 7374:7374 -p 7375:7375 -p 7376:7376 \
  -p 7377:7377 -p 7378:7378 -p 7379:7379 -p 7380:7380 -p 7381:7381 \
  local-mcp
```

## Tests

```bash
pip install -e ".[test]"
pytest
```

## Tools

### Atlassian — port 7373

| Tool | Description |
|------|-------------|
| `jira_search` | Search issues with JQL |
| `jira_get_issue` | Get issue details by key (includes custom fields) |
| `jira_create_issue` | Create a new issue |
| `jira_add_comment` | Add a comment (markdown → ADF by default; optional `comment_format`: `plain`, `adf`) |
| `jira_list_comments` | List all comments on an issue |
| `jira_get_comment` | Get a specific comment by ID |
| `jira_update_custom_field` | Update a custom field on an issue |
| `jira_list_transitions` | List available status transitions |
| `jira_update_status` | Transition an issue to a new status |
| `confluence_search` | Search pages by title or content |
| `confluence_get_page` | Get page content by ID |
| `bitbucket_list_repos` | List workspace repositories |
| `bitbucket_get_repo` | Get repository details |
| `bitbucket_list_branches` | List branches in a repository |
| `bitbucket_get_branch` | Get details of a specific branch |
| `bitbucket_list_commits` | List commits, optionally filtered by branch |
| `bitbucket_get_commit` | Get details of a specific commit |
| `bitbucket_list_prs` | List pull requests (filter by state, branch, author) |
| `bitbucket_get_pr` | Get PR details |
| `bitbucket_get_pr_diff` | Get the full diff of a pull request |
| `bitbucket_list_pr_comments` | List comments on a pull request |
| `bitbucket_create_pr` | Create a new pull request |
| `bitbucket_create_pr_comment` | Post a comment on a pull request |
| `bitbucket_update_pr_description` | Update the description of a PR |
| `bitbucket_update_pr_reviewers` | Replace the reviewer list on a PR |
| `bitbucket_list_branch_restrictions` | List branch restrictions |
| `bitbucket_create_branch_restriction` | Create a branch restriction |
| `bitbucket_list_pipelines` | List recent CI/CD pipelines |
| `bitbucket_get_pipeline` | Get details of a specific pipeline |
| `bitbucket_list_pipeline_steps` | List steps for a pipeline |
| `bitbucket_get_pipeline_step_log` | Get log output for a pipeline step |
| `bitbucket_list_workspace_members` | List workspace members with UUIDs |
| `bitbucket_list_default_reviewers` | List default reviewers for a repository |

### PostgreSQL — port 7374

| Tool | Description |
|------|-------------|
| `pg_query` | Run a read-only SQL query |
| `pg_list_tables` | List tables in a schema |
| `pg_describe_table` | Describe columns of a table |
| `pg_list_indexes` | List indexes on a table |

### Redis — port 7375

| Tool | Description |
|------|-------------|
| `redis_get` | Get the value of a key |
| `redis_keys` | List keys matching a glob pattern |

### Kafka — port 7376

| Tool | Description |
|------|-------------|
| `kafka_list_topics` | List all topics |
| `kafka_describe_topic` | Describe a topic (partitions, replicas, ISR) |
| `kafka_consume` | Consume messages from a topic |

### Figma — port 7377

| Tool | Description |
|------|-------------|
| `figma_get_file` | Get a file's structure and metadata |
| `figma_get_file_nodes` | Get specific nodes by ID |
| `figma_get_images` | Export nodes as images (png, jpg, svg, pdf) |
| `figma_get_comments` | Get all comments on a file |
| `figma_post_comment` | Post or reply to a comment |

### Obsidian — port 7378

| Tool | Description |
|------|-------------|
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

### Elasticsearch + APM — port 7379

| Tool | Description |
|------|-------------|
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

### Loki — port 7380

| Tool | Description |
|------|-------------|
| `loki_search_logs` | Search LogQL across all or one environment and globally sort merged logs |
| `loki_list_labels` | List the union of log labels across environments |
| `loki_list_label_values` | List the union of values for a log label across environments |

### Tempo — port 7381

| Tool | Description |
|------|-------------|
| `tempo_search_traces` | Search TraceQL across all or one environment and merge traces |
| `tempo_get_trace` | Retrieve a trace ID from all or one environment |
| `tempo_list_services` | List the union of traced services across environments |
