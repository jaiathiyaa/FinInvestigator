# backend/app/services/entity_validation.py

from collections import Counter


def select_candidate(
    candidates,
):
    """
    Select a candidate only when both ticker and
    exchange are available from a strong pattern.
    """

    if not candidates:
        return None

    valid = [
        candidate
        for candidate in candidates
        if candidate.get("ticker")
        and candidate.get("exchange")
    ]

    if not valid:
        return None

    ignored_tickers = {
        "THE",
        "AND",
        "FOR",
        "YOUR",
        "STOCK",
        "SHARE",
        "SHARES",
        "PRICE",
        "NEWS",
        "MARKET",
        "USD",
        "INR",
        "CEO",
        "INC",
        "CORP",
        "LTD",
        "LIMITED",
        "SYMBOL",
        "TICKER",
        "EXCHANGE",
        "COMPANY",
        "COMMON",
        "CLASS",
    }

    valid = [
        candidate
        for candidate in valid
        if candidate["ticker"].upper()
        not in ignored_tickers
    ]

    if not valid:
        return None

    combinations = [
        (
            candidate["ticker"].upper(),
            candidate["exchange"].upper(),
        )
        for candidate in valid
    ]

    counts = Counter(combinations)

    best_key, occurrences = (
        counts.most_common(1)[0]
    )

    ticker, exchange = best_key

    matching_candidates = [
        candidate
        for candidate in valid
        if (
            candidate["ticker"].upper(),
            candidate["exchange"].upper(),
        ) == best_key
    ]

    # =====================================================
    # Confidence based on pattern
    # =====================================================

    pattern_confidence = {
        "exchange:ticker": 0.90,
        "ticker:exchange": 0.90,
        "ticker:suffix": 0.85,
    }

    confidence = max(
        pattern_confidence.get(
            candidate.get("pattern"),
            0.70,
        )
        for candidate in matching_candidates
    )

    # Multiple independent results supporting the
    # same candidate increase confidence.

    repetition_bonus = min(
        0.05 * max(
            0,
            occurrences - 1,
        ),
        0.10,
    )

    confidence = min(
        0.99,
        confidence + repetition_bonus,
    )

    return {
        "ticker": ticker,
        "exchange": exchange,
        "confidence": confidence,
        "supporting_results": (
            matching_candidates
        ),
    }