import asyncio
import json

from app.mcp.client import call_search_finance


async def main():

    query = "NVDA:NASDAQ"

    print("=" * 60)
    print("Testing MCP Finance Search")
    print("=" * 60)

    print(f"Query: {query}")
    print()

    try:

        result = await call_search_finance(query)

        print("MCP response received successfully")
        print()

        print("Result type:")
        print(type(result))

        print("\nRaw MCP Result:")
        print(result)

        print("\n" + "=" * 60)
        print("Extracting MCP Content")
        print("=" * 60)

        # MCP CallToolResult contains content
        if hasattr(result, "content"):

            for content in result.content:

                print("\nContent type:")
                print(type(content))

                if hasattr(content, "text"):

                    print("\nText response:")
                    print(content.text)

                    # Try to parse JSON returned by MCP
                    try:

                        data = json.loads(content.text)

                        print("\n" + "=" * 60)
                        print("Parsed Finance Data")
                        print("=" * 60)

                        print("\nEngine:")
                        print(data.get("engine"))

                        print("\nQuery:")
                        print(data.get("query"))

                        print("\nStatus:")
                        print(data.get("status"))

                        print("\nFinance URL:")
                        print(data.get("finance_url"))

                        print("\nMarkets:")
                        print(data.get("markets"))

                        print("\nSummary:")
                        print(data.get("summary"))

                        print("\nGraph:")

                        graph = data.get("graph")

                        if graph:
                            print(
                                f"Graph data received: "
                                f"{len(graph)} points"
                            )

                            print("\nFirst graph point:")
                            print(graph[0])

                        else:
                            print("No graph data returned")

                        print("\nNews:")
                        print(data.get("news"))

                    except json.JSONDecodeError:

                        print(
                            "\nMCP response is not JSON."
                        )

        else:

            print(
                "MCP result does not contain "
                "a content attribute."
            )

        print("\n" + "=" * 60)
        print("Finance MCP test completed")
        print("=" * 60)

    except Exception as exc:

        print("=" * 60)
        print("Finance MCP test failed")
        print("=" * 60)

        print(f"Error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())