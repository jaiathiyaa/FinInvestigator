from typing import Any
import json

from mcp import Client


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"

def _parse_tool_result(result: Any) -> Any:
    """
    Convert MCP CallToolResult into a normal Python object.
    """

    if isinstance(result, dict):
        return result

    if hasattr(result, "content"):

        for content in result.content:

            if not hasattr(
                content,
                "text",
            ):
                continue

            text = content.text

            if not isinstance(
                text,
                str,
            ):
                return text

            text = text.strip()

            if not text:
                return {}

            # -----------------------------------------------------
            # JSON
            # -----------------------------------------------------

            try:

                parsed = json.loads(
                    text
                )

                return parsed

            except json.JSONDecodeError:
                pass

            # -----------------------------------------------------
            # Python representation
            # -----------------------------------------------------

            try:

                import ast

                parsed = ast.literal_eval(
                    text
                )

                return parsed

            except (
                ValueError,
                SyntaxError,
            ):
                pass

            # -----------------------------------------------------
            # Plain text fallback
            # -----------------------------------------------------

            return text

    return result


async def list_tools() -> Any:
    """List all tools exposed by the FinInvestigator MCP server."""

    async with Client(MCP_SERVER_URL) as client:

        return await client.list_tools()


async def call_search_web(query: str) -> Any:
    """Call the web search tool."""

    async with Client(MCP_SERVER_URL) as client:

        result = await client.call_tool(
            "search_web",
            {
                "query": query,
            },
        )

        return _parse_tool_result(result)


async def call_search_news(query: str) -> Any:
    """Call the news search tool."""

    async with Client(MCP_SERVER_URL) as client:

        result = await client.call_tool(
            "search_news",
            {
                "query": query,
            },
        )

        return _parse_tool_result(result)


async def call_resolve_stock(entity: str) -> Any:
    """Resolve a company or stock into ticker and exchange."""

    async with Client(MCP_SERVER_URL) as client:

        result = await client.call_tool(
            "resolve_stock",
            {
                "entity": entity,
            },
        )

        return _parse_tool_result(result)


async def call_search_finance(query: str) -> Any:
    """Call the finance search tool."""

    async with Client(MCP_SERVER_URL) as client:

        result = await client.call_tool(
            "search_finance",
            {
                "query": query,
            },
        )

        return _parse_tool_result(result)