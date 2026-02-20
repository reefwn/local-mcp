from src.tools import mcp, config  # noqa: F401

if config.enable_jira:
    from src.tools import jira  # noqa: F401
if config.enable_confluence:
    from src.tools import confluence  # noqa: F401
if config.enable_bitbucket:
    from src.tools import bitbucket  # noqa: F401


def main():
    mcp.run()


if __name__ == "__main__":
    main()
