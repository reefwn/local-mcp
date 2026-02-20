from mcp.server.fastmcp import FastMCP

from src.clients import AtlassianClient
from src.config import Config

mcp = FastMCP("local-mcp-server")
config = Config()
client = AtlassianClient(config)
