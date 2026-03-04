from mcp.server.fastmcp import FastMCP

from src.clients import AtlassianClient
from src.config import Config

mcp = FastMCP("local-mcp-server", host="0.0.0.0", port=7373)
config = Config()
client = AtlassianClient(config)
