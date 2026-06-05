"""FastMCP server entry point — imports and registers all tool modules."""

from mcp.server.fastmcp import FastMCP

from .tools import admin, assets, changes, cmdb, problems, requests, solutions

mcp = FastMCP("ServiceDesk Plus")

requests.register(mcp)
problems.register(mcp)
changes.register(mcp)
assets.register(mcp)
cmdb.register(mcp)
solutions.register(mcp)
admin.register(mcp)
