import asyncio

from app.services.web_scraper import scrape_page


async def main():

    url = "https://www.nvidia.com/en-us/about-nvidia/"

    try:

        result = await scrape_page(url)

        print("\n==============================")
        print("SCRAPER TEST")
        print("==============================")

        print("URL:")
        print(result["url"])

        print("\nStatus:")
        print(result["status_code"])

        print("\nTitle:")
        print(result["title"])

        print("\nContent Length:")
        print(result["content_length"])

        print("\nContent Preview:")
        print(result["content"][:5000])

    except Exception as exc:

        print("\nSCRAPER ERROR:")
        print(exc)


if __name__ == "__main__":
    asyncio.run(main())