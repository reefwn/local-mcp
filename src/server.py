from src.tools import mcp, config  # noqa: F401

if config.enable_jira:
    from src.tools import jira  # noqa: F401
if config.enable_confluence:
    from src.tools import confluence  # noqa: F401
if config.enable_bitbucket:
    from src.tools import bitbucket  # noqa: F401
if config.enable_postgres:
    from src.tools import postgres  # noqa: F401
if config.enable_redis:
    from src.tools import redis  # noqa: F401
if config.enable_kafka:
    from src.tools import kafka  # noqa: F401


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
