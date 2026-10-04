import json
import os
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


DEFAULT_MODEL = "gpt-4o-mini"


RISK_TYPES = [
    "supply_chain",
    "regulatory",
    "competition",
    "demand_concentration",
    "execution",
    "financial",
    "market_sentiment",
    "technology",
    "geopolitical",
    "operational",
    "none",
]


SYSTEM_PROMPT = """
You are a financial risk classification system.

Your job is to identify whether supplied evidence contains
a genuine potential risk for the investigated company.

IMPORTANT RULES:

1. Do NOT assume that a financial metric is automatically a risk.

2. Positive information such as:
   - revenue growth
   - profit growth
   - strong demand
   - successful partnerships
   - product launches

   is NOT automatically a risk.

3. A risk must represent a potential downside, uncertainty,
   dependency, vulnerability, exposure, or threat.

4. Only use the supplied evidence.

5. Do not introduce external facts.

6. Every identified risk MUST reference the supplied evidence IDs.

7. Do not claim that a risk caused a stock-price movement.

8. Distinguish between:
   - fact
   - potential risk
   - speculation

9. If the evidence does not support a genuine risk,
   return is_risk=false.

10. Confidence must represent confidence that the evidence
    supports the identified risk, NOT confidence that the
    risk will actually occur.

Allowed risk types:

- supply_chain
- regulatory
- competition
- demand_concentration
- execution
- financial
- market_sentiment
- technology
- geopolitical
- operational
- none

Return ONLY valid JSON.

Expected format:

{
  "risks": [
    {
      "risk_type": "supply_chain",
      "is_risk": true,
      "reason": "The evidence indicates dependence on advanced memory supply.",
      "confidence": 0.86,
      "evidence_ids": ["E027", "E029", "E030"]
    }
  ]
}

If no genuine risk is supported:

{
  "risks": []
}
"""


def _get_client() -> ChatOpenAI:

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set."
        )

    model = os.getenv(
        "RISK_MODEL",
        DEFAULT_MODEL,
    )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=0,
    )

def _build_user_prompt(
    company: str,
    evidence: List[Dict[str, Any]],
    causes: Dict[str, Any],
) -> str:

    evidence_lines = []

    for item in evidence:

        evidence_id = item.get(
            "evidence_id",
            "UNKNOWN"
        )

        claim = item.get(
            "claim",
            ""
        )

        claim_type = item.get(
            "claim_type",
            "unknown"
        )

        source = item.get(
            "source",
            "unknown"
        )

        evidence_lines.append(
            f"""
Evidence ID: {evidence_id}
Claim Type: {claim_type}
Source: {source}
Claim: {claim}
""".strip()
        )

    cause_lines = []

    for cause in causes.get(
        "possible_causes",
        []
    ):

        cause_name = cause.get(
            "cause"
        )

        evidence_count = cause.get(
            "evidence_count",
            0
        )

        cause_lines.append(
            f"- {cause_name} "
            f"({evidence_count} evidence items)"
        )

    evidence_text = "\n\n".join(
        evidence_lines
    )

    causes_text = (
        "\n".join(cause_lines)
        if cause_lines
        else "No structured causes were identified."
    )

    return f"""
Company:
{company}

Possible cause categories:
{causes_text}

Evidence:

{evidence_text}

Analyze the supplied evidence.

Identify ONLY genuine potential risks.

Do not treat positive financial performance
as a risk unless the evidence explicitly
contains a downside, uncertainty, dependency,
or vulnerability.

Every risk must reference the evidence IDs
that support it.

Return ONLY valid JSON.
""".strip()


def _parse_response(
    content: str,
) -> Dict[str, Any]:

    content = content.strip()

    # Handle accidental markdown fences.
    if content.startswith("```"):

        lines = content.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    try:

        data = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Risk model returned invalid JSON: "
            f"{exc}"
        ) from exc

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Risk model response must be a JSON object."
        )

    risks = data.get(
        "risks",
        []
    )

    if not isinstance(
        risks,
        list
    ):

        raise ValueError(
            "'risks' must be a JSON list."
        )

    return data


def _validate_risks(
    data: Dict[str, Any],
    valid_evidence_ids: set[str],
) -> List[Dict[str, Any]]:

    validated = []

    for risk in data.get(
        "risks",
        []
    ):

        if not isinstance(
            risk,
            dict
        ):
            continue

        is_risk = risk.get(
            "is_risk",
            True
        )

        if not is_risk:
            continue

        risk_type = risk.get(
            "risk_type",
            "none"
        )

        if risk_type not in RISK_TYPES:
            continue

        if risk_type == "none":
            continue

        evidence_ids = risk.get(
            "evidence_ids",
            []
        )

        if not isinstance(
            evidence_ids,
            list
        ):
            continue

        # Only keep evidence IDs that actually
        # exist in our supplied evidence.
        evidence_ids = [
            evidence_id
            for evidence_id in evidence_ids
            if evidence_id in valid_evidence_ids
        ]

        # A risk without supporting evidence
        # must not enter the final report.
        if not evidence_ids:
            continue

        reason = str(
            risk.get(
                "reason",
                ""
            )
        ).strip()

        if not reason:
            continue

        try:

            confidence = float(
                risk.get(
                    "confidence",
                    0.0
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
                confidence
            )
        )

        validated.append({
            "risk": risk_type,
            "description": reason,
            "confidence": confidence,
            "evidence_count": len(
                evidence_ids
            ),
            "evidence_ids": evidence_ids,
        })

    return validated


async def classify_risks(
    company: str,
    evidence: List[Dict[str, Any]],
    causes: Dict[str, Any],
) -> List[Dict[str, Any]]:

    if not evidence:
        return []

    client = _get_client()

    prompt = _build_user_prompt(
        company=company,
        evidence=evidence,
        causes=causes,
    )

    print(
        "[Risk Classifier] "
        f"Calling model: {DEFAULT_MODEL}"
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

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    if not content:
        raise ValueError(
            "Risk model returned an empty response."
        )

    print(
        "[Risk Classifier] "
        "Model response received"
    )

    parsed = _parse_response(content)

    valid_evidence_ids = {
        item.get("evidence_id")
        for item in evidence
        if item.get("evidence_id")
    }

    validated = _validate_risks(
        parsed,
        valid_evidence_ids,
    )

    print(
        "[Risk Classifier] "
        f"Validated {len(validated)} risks"
    )

    return validated
