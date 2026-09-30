import asyncio

from app.mcp.client import (
    list_tools,
    call_search_web,
    call_search_news,
    call_search_finance,
)


async def main():

    print("\n========== MCP TOOLS ==========\n")

    tools = await list_tools()

    for tool in tools.tools:
        print(f"- {tool.name}")

    print("\n========== WEB SEARCH ==========\n")

    result = await call_search_web(
        "NVIDIA latest developments"
    )

    print(result)

    print("\n========== NEWS SEARCH ==========\n")

    result = await call_search_news(
        "NVIDIA"
    )

    print(result)

    print("\n========== FINANCE SEARCH ==========\n")

    result = await call_search_finance(
        "NVIDIA"
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())