from typing import Any

from mcp import Client


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


async def list_tools() -> Any:
    """List all tools exposed by the FinInvestigator MCP server."""
    async with Client(MCP_SERVER_URL) as client:
        return await client.list_tools()


async def call_search_web(query: str) -> Any:
    """Call the web search tool."""
    async with Client(MCP_SERVER_URL) as client:
        return await client.call_tool(
            "search_web",
            {"query": query},
        )


async def call_search_news(query: str) -> Any:
    """Call the news search tool."""
    async with Client(MCP_SERVER_URL) as client:
        return await client.call_tool(
            "search_news",
            {"query": query},
        )

async def call_resolve_stock(entity: str) -> Any:
    """Resolve a company or stock into ticker and exchange."""

    async with Client(MCP_SERVER_URL) as client:
        result = await client.call_tool(
            "resolve_stock",
            {"entity": entity},
        )

        return result

async def call_search_finance(query: str) -> Any:
    """Call the finance search tool."""
    async with Client(MCP_SERVER_URL) as client:
        return await client.call_tool(
            "search_finance",
            {"query": query},
        )