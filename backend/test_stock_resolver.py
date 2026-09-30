import asyncio
import json

from app.mcp.client import call_resolve_stock


async def main():

    entities = [
        "Airtel",
    ]

    for entity in entities:

        print("\n")
        print("=" * 60)
        print(f"Resolving: {entity}")
        print("=" * 60)

        try:

            result = await call_resolve_stock(
                entity
            )

            print("\nMCP Result:")
            print(result)

            # ---------------------------------------------
            # Try to print the actual returned JSON
            # ---------------------------------------------

            if hasattr(result, "content"):

                for item in result.content:

                    if hasattr(item, "text"):

                        print("\nParsed Result:")

                        try:

                            parsed = json.loads(
                                item.text
                            )

                            print(
                                json.dumps(
                                    parsed,
                                    indent=2,
                                )
                            )

                        except json.JSONDecodeError:

                            print(
                                item.text
                            )

        except Exception as exc:

            print("\nERROR:")
            print(type(exc).__name__)
            print(str(exc))


if __name__ == "__main__":

    asyncio.run(main())