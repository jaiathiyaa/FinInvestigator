# backend/app/services/llm_evidence_extractor.py

from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

from app.services.llm_entity_resolver import (
    get_openai_client,
)


class EvidenceTickerResolution(BaseModel):

    ticker: Optional[str] = None

    exchange: Optional[str] = None

    confidence: float

    reasoning: str

    evidence_indices: list[int]


def resolve_ticker_from_search_results(
    company_name: str,
    search_results: list[dict],
) -> EvidenceTickerResolution:

    client: OpenAI = get_openai_client()

    # =====================================================
    # Prepare search results for the LLM
    # =====================================================

    formatted_results = []

    for index, result in enumerate(
        search_results
    ):

        formatted_results.append(
            f"""
RESULT {index}

Title:
{result.get("title", "")}

Snippet:
{result.get("snippet", "")}

URL:
{result.get("url", "")}
"""
        )

    evidence_text = "\n".join(
        formatted_results
    )

    # =====================================================
    # LLM
    # =====================================================

    response = client.responses.parse(
        model="gpt-40-mini",
        input=[
            {
                "role": "system",
                "content": """
You are a financial evidence extraction system.

Your task is to identify the stock ticker and
stock exchange of the requested company using
ONLY the supplied web search results.

IMPORTANT RULES:

1. Use ONLY the supplied search results.

2. Do NOT use your own prior knowledge.

3. Do NOT guess.

4. Do NOT invent a ticker.

5. Do NOT invent an exchange.

6. Make sure the ticker belongs to the requested
   company.

7. Prefer explicit evidence such as:

   NASDAQ:MSFT
   MSFT:NASDAQ
   Microsoft Corporation (MSFT)
   MSFT.US
   NSE:RELIANCE
   RELIANCE.NS

8. If the search results clearly identify the
   ticker but do not provide enough evidence for
   the exchange, return the ticker and set
   exchange to null.

9. If the ticker cannot be reliably identified,
   return ticker=null and exchange=null.

10. Confidence must represent confidence based
    ONLY on the supplied evidence.

11. evidence_indices must contain the indexes
    of the search results that support the answer.

12. Do not treat ordinary words such as:

    MAY
    SYMBOL
    COMPANY
    COMMON
    PRICE
    STOCK
    MARKET
    EXCHANGE

    as ticker symbols unless the search evidence
    explicitly identifies them as the company's
    ticker.

Return the strongest evidence-supported candidate.
""",
            },
            {
                "role": "user",
                "content": f"""
Requested company:

{company_name}

Web search results:

{evidence_text}
""",
            },
        ],
        text_format=EvidenceTickerResolution,
    )

    return response.output_parsed