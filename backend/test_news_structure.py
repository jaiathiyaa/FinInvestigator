import asyncio

from app.mcp.client import call_search_news


async def main():

    print("=" * 70)
    print("TESTING NEWS RESPONSE STRUCTURE")
    print("=" * 70)

    query = "NVIDIA latest news"

    print(f"\nQuery:")
    print(query)

    try:

        result = await call_search_news(query)

        print("\n" + "=" * 70)
        print("RESULT TYPE")
        print("=" * 70)

        print(type(result))

        print("\n" + "=" * 70)
        print("TOP LEVEL KEYS")
        print("=" * 70)

        if isinstance(result, dict):

            for key in result.keys():
                print(f"  - {key}")

        else:

            print("Result is not a dictionary.")

        print("\n" + "=" * 70)
        print("FULL RESULT")
        print("=" * 70)

        print(result)

        if isinstance(result, dict):

            print("\n" + "=" * 70)
            print("POSSIBLE ARTICLE FIELDS")
            print("=" * 70)

            for key in [
                "news",
                "news_results",
                "articles",
                "results",
                "organic_results",
            ]:

                value = result.get(key)

                print(f"\n{key}:")

                if value is None:

                    print("  None")

                elif isinstance(value, list):

                    print(
                        f"  List with {len(value)} items"
                    )

                    if value:

                        print("\n  First item:")

                        print(value[0])

                else:

                    print(type(value))
                    print(value)

    except Exception as exc:

        print("\n" + "=" * 70)
        print("TEST FAILED")
        print("=" * 70)

        print(f"\nError: {exc}")
        print(f"Error Type: {type(exc).__name__}")


if __name__ == "__main__":
    asyncio.run(main())