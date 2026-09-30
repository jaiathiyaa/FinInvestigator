from typing import Optional

from openai import OpenAI
from pydantic import BaseModel


class EntityResolution(BaseModel):
    entity_type: str
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    confidence: float
    reasoning: str


def get_openai_client() -> OpenAI:

    import os

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(
        api_key=api_key
    )


def resolve_entity_with_llm(
    entity: str,
) -> EntityResolution:

    client = get_openai_client()

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": """
You are a financial entity resolution system.

Identify the company/security that the
user is referring to.

Examples:

NVIDIA
-> NVIDIA Corporation

NVDA
-> NVIDIA Corporation

Reliance
-> Reliance Industries Limited

TCS
-> Tata Consultancy Services Limited

Microsoft
-> Microsoft Corporation

Tesla
-> Tesla, Inc.

Important:

- Identify the company carefully.
- Ticker and exchange are only candidates.
- Never invent a ticker.
- If uncertain, return null.
- Do not use words from the prompt such as
  "stock", "share", "your", "price", etc.
  as a ticker.
- Confidence represents confidence in the
  company identification.
""",
            },
            {
                "role": "user",
                "content": (
                    f"Resolve this financial entity: "
                    f"{entity}"
                ),
            },
        ],
        text_format=EntityResolution,
    )

    return response.output_parsed