from __future__ import annotations

from typing import Any, Dict, Optional


# ============================================================
# DIRECTION NORMALIZATION
# ============================================================

UP_DIRECTIONS = {
    "up",
    "rise",
    "rising",
    "rose",
    "gain",
    "gained",
    "gains",
    "increase",
    "increased",
    "increasing",
    "higher",
    "positive",
}


DOWN_DIRECTIONS = {
    "down",
    "fall",
    "falling",
    "fell",
    "drop",
    "dropped",
    "drops",
    "decline",
    "declined",
    "declining",
    "lower",
    "negative",
}


FLAT_DIRECTIONS = {
    "flat",
    "unchanged",
    "neutral",
    "no_change",
    "no change",
}


def normalize_direction(
    value: Any,
) -> str:
    """
    Normalize arbitrary direction text.

    Returns:

        up
        down
        flat
        unknown
    """

    if value is None:
        return "unknown"

    value = str(
        value
    ).strip().lower()

    if value in UP_DIRECTIONS:
        return "up"

    if value in DOWN_DIRECTIONS:
        return "down"

    if value in FLAT_DIRECTIONS:
        return "flat"

    return "unknown"


# ============================================================
# PERCENTAGE CHANGE
# ============================================================

def parse_numeric_change(
    value: Any,
) -> Optional[float]:
    """
    Convert common numeric/string percentage values into float.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (int, float),
    ):
        return float(value)

    if isinstance(
        value,
        str,
    ):
        cleaned = (
            value
            .replace("%", "")
            .replace("+", "")
            .replace(",", "")
            .strip()
        )

        try:
            return float(cleaned)

        except ValueError:
            return None

    return None


def direction_from_percent_change(
    change: Any,
) -> str:
    """
    Convert percentage movement to direction.
    """

    value = parse_numeric_change(
        change
    )

    if value is None:
        return "unknown"

    if value > 0:
        return "up"

    if value < 0:
        return "down"

    return "flat"


# ============================================================
# RECURSIVE MARKET DATA SEARCH
# ============================================================

def _extract_change_recursive(
    data: Any,
) -> Optional[float]:
    """
    Recursively search the market response for a percentage
    change field.

    This supports several common SerpApi/Google Finance
    response structures.
    """

    if isinstance(
        data,
        dict,
    ):

        preferred_keys = [
            "change_percent",
            "change_percentage",
            "percent_change",
            "percentage_change",
            "price_change_percent",
            "price_change_percentage",
            "change_pct",
            "changePercent",
            "percentChange",
        ]

        # ----------------------------------------------------
        # First pass: explicit percentage fields
        # ----------------------------------------------------

        for key in preferred_keys:

            if key not in data:
                continue

            value = parse_numeric_change(
                data[key]
            )

            if value is not None:
                return value

        # ----------------------------------------------------
        # Second pass: nested dictionaries
        # ----------------------------------------------------

        for value in data.values():

            result = _extract_change_recursive(
                value
            )

            if result is not None:
                return result

    elif isinstance(
        data,
        list,
    ):

        for item in data:

            result = _extract_change_recursive(
                item
            )

            if result is not None:
                return result

    return None


def _extract_direction_recursive(
    data: Any,
) -> Optional[str]:
    """
    Recursively search the market response for an explicit
    direction field.
    """

    if isinstance(
        data,
        dict,
    ):

        preferred_keys = [
            "direction",
            "price_direction",
            "movement",
            "trend",
            "price_movement",
        ]

        # ----------------------------------------------------
        # Explicit direction
        # ----------------------------------------------------

        for key in preferred_keys:

            if key not in data:
                continue

            direction = normalize_direction(
                data[key]
            )

            if direction != "unknown":
                return direction

        # ----------------------------------------------------
        # Nested search
        # ----------------------------------------------------

        for value in data.values():

            result = _extract_direction_recursive(
                value
            )

            if result is not None:
                return result

    elif isinstance(
        data,
        list,
    ):

        for item in data:

            result = _extract_direction_recursive(
                item
            )

            if result is not None:
                return result

    return None


# ============================================================
# MAIN VERIFIER
# ============================================================

def verify_movement(
    requested_direction: str,
    market_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verify whether the market data supports the direction
    requested by the user.

    Example:

        requested = "down"

        market_data:
            change_percent = +2.5

        result:
            requested_direction = "down"
            actual_direction = "up"
            matches_request = False
            verified = True
    """

    requested = normalize_direction(
        requested_direction
    )

    # --------------------------------------------------------
    # Extract explicit direction
    # --------------------------------------------------------

    actual = _extract_direction_recursive(
        market_data
    )

    # --------------------------------------------------------
    # Extract percentage change
    # --------------------------------------------------------

    change_percent = _extract_change_recursive(
        market_data
    )

    # --------------------------------------------------------
    # Percentage is more concrete than a vague text trend.
    #
    # If percentage is available, use it.
    # --------------------------------------------------------

    if change_percent is not None:

        actual_from_change = (
            direction_from_percent_change(
                change_percent
            )
        )

        if actual_from_change != "unknown":
            actual = actual_from_change

    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    if actual is None:
        actual = "unknown"

    # --------------------------------------------------------
    # Determine match
    # --------------------------------------------------------

    matches_request = False

    if (
        requested in {"up", "down"}
        and actual in {"up", "down"}
    ):

        matches_request = (
            requested == actual
        )

    elif (
        requested == "flat"
        and actual == "flat"
    ):

        matches_request = True

    # --------------------------------------------------------
    # Verified means we actually know the movement
    # --------------------------------------------------------

    verified = actual != "unknown"

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    if actual == "up":

        if change_percent is not None:

            explanation = (
                "The available market data shows "
                f"the stock rising "
                f"({change_percent:+.2f}%)."
            )

        else:

            explanation = (
                "The available market data shows "
                "the stock rising."
            )

    elif actual == "down":

        if change_percent is not None:

            explanation = (
                "The available market data shows "
                f"the stock falling "
                f"({change_percent:+.2f}%)."
            )

        else:

            explanation = (
                "The available market data shows "
                "the stock falling."
            )

    elif actual == "flat":

        explanation = (
            "The available market data does not "
            "show a meaningful upward or downward "
            "movement."
        )

    else:

        explanation = (
            "The available market data does not "
            "contain enough information to verify "
            "the requested price movement."
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "requested_direction": requested,
        "actual_direction": actual,
        "matches_request": matches_request,
        "verified": verified,
        "change_percent": change_percent,
        "explanation": explanation,
    }