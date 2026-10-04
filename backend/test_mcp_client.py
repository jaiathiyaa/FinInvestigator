import asyncio
import json

from app.mcp.client import call_search_finance


async def main():

    print("=" * 60)
    print("Testing MCP Client")
    print("=" * 60)

    query = "NVDA:NASDAQ"

    print(f"\nFinance Query: {query}")

    try:

        result = await call_search_finance(query)

        print("\nMCP Client call completed")

        print("\nResult Type:")
        print(type(result))

        print("\n" + "=" * 60)
        print("Client Result")
        print("=" * 60)

        print(result)

        # Check whether client returned a dictionary
        if isinstance(result, dict):

            print("\n✓ Client returned a Python dictionary")

            print("\nEngine:")
            print(result.get("engine"))

            print("\nQuery:")
            print(result.get("query"))

            print("\nStatus:")
            print(result.get("status"))

            print("\nFinance URL:")
            print(result.get("finance_url"))

            print("\nSummary:")
            print(result.get("summary"))

            graph = result.get("graph")

            print("\nGraph:")

            if graph:
                print(f"✓ {len(graph)} graph points received")
                print("\nFirst graph point:")
                print(graph[0])
            else:
                print("No graph data returned")

            print("\nNews:")
            print(result.get("news"))

        else:

            print(
                "\n✗ Client did not return a dictionary."
            )

            print(
                "Returned type:",
                type(result)
            )

            print(
                "\nYour app/mcp/client.py probably "
                "still returns CallToolResult directly."
            )

        print("\n" + "=" * 60)
        print("MCP Client Test Completed")
        print("=" * 60)

    except Exception as exc:

        print("\n" + "=" * 60)
        print("MCP Client Test Failed")
        print("=" * 60)

        print(f"\nError: {exc}")
        print(f"Error Type: {type(exc).__name__}")


if __name__ == "__main__":
    asyncio.run(main())