from typing import Any, Dict, List
import ast
import json

from app.graph.state import InvestigationState
from app.mcp.client import call_search_news
from app.services.web_scraper import scrape_page
from app.services.source_selector import select_sources


MAX_ARTICLES_TO_SCRAPE = 5
CANDIDATE_SOURCES = 12


def _normalize_news_result(
    result: Any,
) -> Dict[str, Any]:
    """
    Normalize MCP news response.

    Supports:
    - dict
    - JSON string
    - Python dictionary string
    """

    if isinstance(result, dict):
        return result

    if isinstance(result, str):

        text = result.strip()

        if not text:
            return {}

        # Try JSON.
        try:

            parsed = json.loads(text)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        # Try Python dict representation.
        try:

            parsed = ast.literal_eval(text)

            if isinstance(parsed, dict):
                return parsed

        except (
            ValueError,
            SyntaxError,
        ):
            pass

    print(
        "[News Agent] Unexpected MCP response type: "
        f"{type(result).__name__}"
    )

    return {}


async def news_agent(
    state: InvestigationState,
) -> InvestigationState:

    company = state["company"]

    print(
        f"[News Agent] Searching news for {company}"
    )

    query = f"{company} latest news"

    try:

        # ---------------------------------------------------------
        # MCP search
        # ---------------------------------------------------------

        raw_result = await call_search_news(
            query
        )

        print(
            "[News Agent] MCP response type: "
            f"{type(raw_result).__name__}"
        )

        result = _normalize_news_result(
            raw_result
        )

        if not result:

            print(
                "[News Agent] MCP returned an empty "
                "or invalid response"
            )

            return {
                "news_data": {
                    "query": query,
                    "search_results": [],
                    "selected_sources": [],
                    "articles": [],
                    "successful_articles": 0,
                    "failed_articles": 0,
                    "agent": "news_agent",
                    "source_type": "news",
                    "error": (
                        "Invalid or empty MCP news response."
                    ),
                    "error_type": (
                        "invalid_mcp_response"
                    ),
                }
            }

        # ---------------------------------------------------------
        # Extract results
        # ---------------------------------------------------------

        news_results = result.get(
            "news_results",
            [],
        )

        if not isinstance(
            news_results,
            list,
        ):

            print(
                "[News Agent] "
                "'news_results' is not a list. "
                f"Received: "
                f"{type(news_results).__name__}"
            )

            news_results = []

        print(
            f"[News Agent] Found "
            f"{len(news_results)} search results"
        )

        # ---------------------------------------------------------
        # Select a larger candidate pool.
        #
        # We may lose some sources because of 401/403.
        # ---------------------------------------------------------

        selected_sources = select_sources(
            news_results=news_results,
            company=company,
            query=state.get(
                "query",
                "",
            ),
            limit=CANDIDATE_SOURCES,
        )

        print(
            f"[News Agent] Selected "
            f"{len(selected_sources)} candidates"
        )

        # ---------------------------------------------------------
        # Debug candidate ranking
        # ---------------------------------------------------------

        for index, source in enumerate(
            selected_sources,
            start=1,
        ):

            print(
                f"[News Agent] Candidate {index}: "
                f"{source.get('title')} | "
                f"domain={source.get('_domain')} | "
                f"score={source.get('_selection_score')} | "
                f"investigation="
                f"{source.get('_investigation_relevance')} | "
                f"recency="
                f"{source.get('_recency_score')}"
            )

        # ---------------------------------------------------------
        # Scrape candidates until we have 5 successes.
        # ---------------------------------------------------------

        articles: List[Dict[str, Any]] = []

        attempted = 0
        failed = 0

        for index, article in enumerate(
            selected_sources,
            start=1,
        ):

            # Stop once enough usable articles exist.
            if len(articles) >= MAX_ARTICLES_TO_SCRAPE:
                break

            if not isinstance(
                article,
                dict,
            ):
                continue

            url = article.get(
                "link"
            )

            if not url:
                print(
                    f"[News Agent] "
                    f"Skipping candidate {index}: "
                    f"no URL"
                )
                continue

            title = article.get(
                "title",
                "Untitled",
            )

            source_data = article.get(
                "source"
            ) or {}

            if isinstance(
                source_data,
                dict,
            ):
                source_name = source_data.get(
                    "name",
                    "Unknown",
                )
            else:
                source_name = str(
                    source_data
                )

            attempted += 1

            print(
                f"[News Agent] "
                f"Scraping candidate "
                f"{index}/{len(selected_sources)}: "
                f"{title}"
            )

            try:

                scraped = await scrape_page(
                    url
                )

                if not isinstance(
                    scraped,
                    dict,
                ):
                    raise TypeError(
                        "Scraper returned "
                        f"{type(scraped).__name__} "
                        "instead of dict"
                    )

                content = scraped.get(
                    "content",
                    "",
                )

                content_length = scraped.get(
                    "content_length",
                    0,
                )

                # -------------------------------------------------
                # Reject empty or useless pages.
                # -------------------------------------------------

                if (
                    not content
                    or content_length < 200
                ):
                    raise ValueError(
                        "Scraped page contains "
                        "insufficient content."
                    )

                articles.append(
                    {
                        "title": title,
                        "source": source_name,
                        "url": scraped.get(
                            "url",
                            url,
                        ),
                        "date": (
                            article.get(
                                "iso_date"
                            )
                            or article.get(
                                "date"
                            )
                        ),
                        "content": content,
                        "content_length": (
                            content_length
                        ),
                        "scrape_status": "success",
                    }
                )

                print(
                    f"[News Agent] "
                    f"Scrape successful "
                    f"({len(articles)}/"
                    f"{MAX_ARTICLES_TO_SCRAPE}) "
                    f"- {content_length} chars"
                )

            except Exception as exc:

                failed += 1

                print(
                    f"[News Agent] "
                    f"Candidate failed: {exc}"
                )

                # IMPORTANT:
                # Failed sources are NOT added to articles.
                continue

        # ---------------------------------------------------------
        # Final statistics
        # ---------------------------------------------------------

        successful_articles = len(
            articles
        )

        print(
            "[News Agent] Successfully scraped: "
            f"{successful_articles}"
        )

        print(
            "[News Agent] Failed candidates: "
            f"{failed}"
        )

        print(
            "[News Agent] Candidates attempted: "
            f"{attempted}"
        )

        # ---------------------------------------------------------
        # Return
        # ---------------------------------------------------------

        return {
            "news_data": {
                "query": query,
                "search_results": news_results,
                "selected_sources": selected_sources,
                "articles": articles,
                "successful_articles": (
                    successful_articles
                ),
                "failed_articles": failed,
                "candidate_count": len(
                    selected_sources
                ),
                "agent": "news_agent",
                "source_type": "news",
            }
        }

    except Exception as exc:

        print(
            f"[News Agent] Search error: {exc}"
        )

        return {
            "news_data": {
                "query": query,
                "search_results": [],
                "selected_sources": [],
                "articles": [],
                "successful_articles": 0,
                "failed_articles": 0,
                "candidate_count": 0,
                "agent": "news_agent",
                "source_type": "news",
                "error": str(exc),
                "error_type": "news_search_error",
            }
        }