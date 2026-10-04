from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.movement_verifier import verify_movement


def movement_verification_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verify whether the requested stock movement is actually
    supported by the market data.

    Example:

        User:
            Why did NVIDIA stock fall?

        Requested:
            down

        Market:
            +2.5%

        Result:
            requested = down
            actual = up
            matches = False

    When there is a mismatch, causal analysis must not be
    performed.
    """

    query = state.get(
        "query",
        "",
    )

    company = state.get(
        "company",
        "",
    )

    requested_direction = state.get(
        "price_direction",
        "unknown",
    )

    market_data = state.get(
        "market_data",
        {},
    )

    print("\n" + "=" * 60)
    print("[Movement Agent] Verifying price movement")
    print("=" * 60)

    print(
        f"[Movement Agent] Query: {query}"
    )

    print(
        f"[Movement Agent] Company: {company}"
    )

    print(
        f"[Movement Agent] Requested direction: "
        f"{requested_direction}"
    )

    # --------------------------------------------------------
    # Verify movement
    # --------------------------------------------------------

    result = verify_movement(
        requested_direction=requested_direction,
        market_data=market_data,
    )

    actual_direction = result.get(
        "actual_direction",
        "unknown",
    )

    matches_request = result.get(
        "matches_request",
        False,
    )

    verified = result.get(
        "verified",
        False,
    )

    change_percent = result.get(
        "change_percent",
    )

    # --------------------------------------------------------
    # Logging
    # --------------------------------------------------------

    print(
        f"[Movement Agent] Actual direction: "
        f"{actual_direction}"
    )

    print(
        f"[Movement Agent] Change percent: "
        f"{change_percent}"
    )

    print(
        f"[Movement Agent] Verified: "
        f"{verified}"
    )

    print(
        f"[Movement Agent] Matches request: "
        f"{matches_request}"
    )

    print(
        f"[Movement Agent] Explanation: "
        f"{result.get('explanation', '')}"
    )

    # --------------------------------------------------------
    # Determine mismatch
    # --------------------------------------------------------

    movement_mismatch = (
        requested_direction in {"up", "down"}
        and verified
        and not matches_request
        and actual_direction in {"up", "down"}
    )

    if movement_mismatch:
        print(
            "[Movement Agent] ⚠️ Requested movement "
            "does NOT match actual movement."
        )

        print(
            "[Movement Agent] Causal analysis should "
            "NOT be performed."
        )

    elif (
        requested_direction in {"up", "down"}
        and not verified
    ):
        print(
            "[Movement Agent] ⚠️ Unable to verify "
            "requested movement."
        )

        print(
            "[Movement Agent] Causal analysis should "
            "NOT be performed."
        )

    else:
        print(
            "[Movement Agent] ✅ Requested movement "
            "is supported."
        )

    # --------------------------------------------------------
    # Trace
    # --------------------------------------------------------

    trace = list(
        state.get(
            "trace",
            [],
        )
    )

    trace.append(
        {
            "agent": "movement_verification",
            "status": "completed",
            "requested_direction": requested_direction,
            "actual_direction": actual_direction,
            "verified": verified,
            "matches_request": matches_request,
            "movement_mismatch": movement_mismatch,
        }
    )

    # --------------------------------------------------------
    # Return state updates
    # --------------------------------------------------------

    return {
        "movement_verification": result,
        "movement_mismatch": movement_mismatch,
        "trace": trace,
    }