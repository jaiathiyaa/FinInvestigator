import asyncio

from app.agents.market_agent import market_agent


async def main():

    state = {
        "query": "investigate NVIDIA",
        "company": "NVIDIA"
    }

    print("=" * 60)
    print("Testing Market Agent")
    print("=" * 60)

    try:

        result = await market_agent(state)

        print("\nMarket Agent Result:")
        print(result)

        market_data = result.get("market_data", {})

        print("\n" + "=" * 60)
        print("Market Data")
        print("=" * 60)

        print("\nCompany:")
        print(market_data.get("company"))

        print("\nTicker:")
        print(market_data.get("ticker"))

        print("\nExchange:")
        print(market_data.get("exchange"))

        print("\nFinance Query:")
        print(market_data.get("query"))

        print("\nSource:")
        print(market_data.get("source_type"))

        print("\nResolution:")
        print(market_data.get("resolution"))

        finance_result = market_data.get("result")

        if finance_result:

            print("\nFinance Status:")
            print(finance_result.get("status"))

            print("\nFinance URL:")
            print(finance_result.get("finance_url"))

            print("\nSummary:")
            print(finance_result.get("summary"))

            graph = finance_result.get("graph")

            if graph:
                print(
                    f"\nGraph Points: {len(graph)}"
                )

        print("\n" + "=" * 60)
        print("Market Agent Test Completed")
        print("=" * 60)

    except Exception as exc:

        print("\nMarket Agent Test Failed")
        print(f"Error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())