import os
from typing import Any

import serpapi
from mcp.server.mcpserver import MCPServer
from dotenv import load_dotenv
from app.services.stock_resolver import resolve_stock as resolve_stock_service

mcp = MCPServer(
    "FinInvestigator Search",
    instructions=(
        "Search tools for the FinInvestigator financial research system. "
        "Use these tools to retrieve current web, news, and financial information."
    ),
)

load_dotenv()

def get_serpapi_client() -> serpapi.Client:
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "SERPAPI_API_KEY is not configured in the environment."
        )

    return serpapi.Client(
        api_key=api_key,
        timeout=15,
    )


def normalize_result(result: Any) -> dict:
    """
    Convert SerpApi response into a JSON-friendly dictionary.
    """

    if isinstance(result, dict):
        return dict(result)

    return dict(result)


@mcp.tool()
def search_web(query: str) -> dict:
    """
    Search the web for current information.

    Args:
        query: Search query.

    Returns:
        Normalized SerpApi Google search results.
    """

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    client = get_serpapi_client()

    results = client.search(
        {
            "engine": "google",
            "q": query,
            "output": "json",
        }
    )

    data = normalize_result(results)

    return {
        "engine": "google",
        "query": query,
        "organic_results": data.get("organic_results", []),
        "knowledge_graph": data.get("knowledge_graph"),
        "answer_box": data.get("answer_box"),
        "search_metadata": data.get("search_metadata"),
    }


@mcp.tool()
def search_news(query: str) -> dict:
    """
    Search recent news related to a financial topic.

    Args:
        query: News search query.

    Returns:
        Normalized SerpApi Google News results.
    """

    if not query.strip():
        raise ValueError("News query cannot be empty.")

    client = get_serpapi_client()

    results = client.search(
        {
            "engine": "google_news",
            "q": query,
            "output": "json",
        }
    )

    data = normalize_result(results)

    return {
        "engine": "google_news",
        "query": query,
        "news_results": data.get("news_results", []),
        "search_metadata": data.get("search_metadata"),
    }

@mcp.tool()
def resolve_stock(entity: str) -> dict:
    """
    Resolve a financial entity using
    cached mappings, LLM interpretation,
    web evidence, and SerpApi Finance
    verification.
    """

    return resolve_stock_service(entity)

@mcp.tool()
def search_finance(query: str) -> dict:
    if not query.strip():
        raise ValueError("Finance query cannot be empty.")

    client = get_serpapi_client()

    results = client.search({
        "engine": "google_finance",
        "q": query,
        "output": "json",
    })

    data = normalize_result(results)

    return {
        "engine": "google_finance",
        "query": query,
        "status": data.get("search_metadata", {}).get("status"),
        "finance_url": data.get("search_metadata", {}).get(
            "google_finance_url"
        ),
        "markets": data.get("markets"),
        "summary": data.get("summary"),
        "graph": data.get("graph"),
        "news": data.get("news"),
        "search_metadata": data.get("search_metadata"),
    }
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
    )