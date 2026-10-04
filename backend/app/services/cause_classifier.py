import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


DEFAULT_MODEL = "gpt-4o-mini"


CAUSE_TYPES = [
    "earnings",
    "business_growth",
    "partnership",
    "product_launch",
    "acquisition",
    "regulation",
    "analyst_activity",
    "market_sentiment",
    "technology_demand",
    "capital_allocation",
    "supply_chain",
    "none",
]


SYSTEM_PROMPT = """
You are a financial investigation cause-classification system.

Your job is to identify evidence-supported possible catalysts
or explanations relevant to an investigation of a company.

IMPORTANT RULES:

1. Only use the supplied evidence.

2. Do NOT introduce external facts.

3. Do NOT assume that every piece of evidence is a cause.

4. Positive financial performance such as:
   - revenue growth
   - profit growth
   - strong demand
   - successful partnerships
   - product launches

   may be relevant evidence, but they must only be classified
   as a possible cause when they are genuinely relevant to the
   investigation.

5. A cause represents a plausible explanation or catalyst
   supported by the supplied evidence.

6. Do NOT claim that the evidence proves direct causality.

7. Distinguish between:
   - documented fact
   - plausible catalyst
   - speculation

8. Every identified cause MUST reference one or more supplied
   evidence IDs.

9. Never invent evidence IDs.

10. Ignore evidence that does not meaningfully support a cause.

11. Do not classify an evidence item into a category merely
    because it contains a keyword associated with that category.

12. Semantic meaning is more important than keyword matching.

13. Confidence represents how strongly the supplied evidence
    supports the possible cause, NOT the probability that the
    cause actually caused the event.

Allowed cause types:

- earnings
- business_growth
- partnership
- product_launch
- acquisition
- regulation
- analyst_activity
- market_sentiment
- technology_demand
- capital_allocation
- supply_chain
- none

Return ONLY valid JSON.

Expected format:

{
  "causes": [
    {
      "cause_type": "earnings",
      "reason": "The evidence reports strong quarterly financial performance.",
      "confidence": 0.94,
      "evidence_ids": ["E002", "E004"]
    }
  ]
}

If no meaningful causes are supported:

{
  "causes": []
}
"""


def _get_client() -> ChatOpenAI:

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set."
        )

    model = os.getenv(
        "CAUSE_MODEL",
        DEFAULT_MODEL,
    )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=0,
    )


def _build_user_prompt(
    company: str,
    query: str,
    evidence: List[Dict[str, Any]],
) -> str:

    evidence_lines = []

    for item in evidence:

        evidence_id = item.get(
            "evidence_id",
            "UNKNOWN",
        )

        claim = item.get(
            "claim",
            "",
        )

        claim_type = item.get(
            "claim_type",
            "unknown",
        )

        source = item.get(
            "source",
            "unknown",
        )

        date = item.get(
            "date",
            "unknown",
        )

        evidence_lines.append(
            f"""
Evidence ID: {evidence_id}
Claim Type: {claim_type}
Source: {source}
Date: {date}
Claim: {claim}
""".strip()
        )

    evidence_text = "\n\n".join(
        evidence_lines
    )

    return f"""
Company:
{company}

Investigation Query:
{query}

Evidence:

{evidence_text}

Analyze the supplied evidence.

Identify only meaningful possible causes or catalysts
relevant to the investigation.

Do not force evidence into a cause category.

Do not use keyword matching.

Every cause must reference the evidence IDs that
actually support it.

Do not claim direct causality.

Return ONLY valid JSON.
""".strip()


def _parse_response(
    content: str,
) -> Dict[str, Any]:

    content = content.strip()

    # Remove accidental markdown fences.
    if content.startswith("```"):

        lines = content.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(
            lines
        ).strip()

    try:

        data = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Cause model returned invalid JSON: "
            f"{exc}"
        ) from exc

    if not isinstance(
        data,
        dict,
    ):

        raise ValueError(
            "Cause model response must be a JSON object."
        )

    causes = data.get(
        "causes",
        [],
    )

    if not isinstance(
        causes,
        list,
    ):

        raise ValueError(
            "'causes' must be a JSON list."
        )

    return data

def _validate_causes(
    data: Dict[str, Any],
    valid_evidence_ids: set[str],
) -> List[Dict[str, Any]]:

    grouped: Dict[str, Dict[str, Any]] = {}

    for cause in data.get(
        "causes",
        [],
    ):

        if not isinstance(
            cause,
            dict,
        ):
            continue

        cause_type = cause.get(
            "cause_type",
            "none",
        )

        if cause_type not in CAUSE_TYPES:
            continue

        if cause_type == "none":
            continue

        evidence_ids = cause.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            evidence_ids,
            list,
        ):
            continue

        evidence_ids = [
            evidence_id
            for evidence_id in evidence_ids
            if evidence_id in valid_evidence_ids
        ]

        if not evidence_ids:
            continue

        reason = str(
            cause.get(
                "reason",
                "",
            )
        ).strip()

        if not reason:
            continue

        try:
            confidence = float(
                cause.get(
                    "confidence",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        if cause_type not in grouped:

            grouped[cause_type] = {
                "cause": cause_type,
                "description": reason,
                "confidence": confidence,
                "evidence_ids": [],
            }

        else:

            existing = grouped[cause_type]

            # Keep the stronger confidence.
            existing["confidence"] = max(
                existing["confidence"],
                confidence,
            )

            # Combine explanations.
            if reason not in existing["description"]:
                existing["description"] += (
                    " " + reason
                )

        # Merge evidence IDs.
        for evidence_id in evidence_ids:

            if evidence_id not in grouped[
                cause_type
            ]["evidence_ids"]:

                grouped[
                    cause_type
                ]["evidence_ids"].append(
                    evidence_id
                )

    validated = []

    for cause in grouped.values():

        cause["evidence_count"] = len(
            cause["evidence_ids"]
        )

        validated.append(
            cause
        )

    return validated


async def classify_causes(
    company: str,
    query: str,
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    if not evidence:
        return []

    client = _get_client()

    model = os.getenv(
        "CAUSE_MODEL",
        DEFAULT_MODEL,
    )

    prompt = _build_user_prompt(
        company=company,
        query=query,
        evidence=evidence,
    )

    print(
        "[Cause Classifier] "
        f"Calling model: {model}"
    )

    response = await client.ainvoke(
        [
            (
                "system",
                SYSTEM_PROMPT,
            ),
            (
                "human",
                prompt,
            ),
        ]
    )

    content = response.content

    if isinstance(
        content,
        list,
    ):

        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    if not content:

        raise ValueError(
            "Cause model returned an empty response."
        )

    print(
        "[Cause Classifier] "
        "Model response received"
    )

    parsed = _parse_response(
        content
    )

    valid_evidence_ids = {
        item.get("evidence_id")
        for item in evidence
        if item.get("evidence_id")
    }

    validated = _validate_causes(
        parsed,
        valid_evidence_ids,
    )

    print(
        "[Cause Classifier] "
        f"Validated {len(validated)} causes"
    )

    return validated