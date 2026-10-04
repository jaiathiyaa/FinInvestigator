from __future__ import annotations

from typing import Any, Dict
import inspect
from langgraph.graph import StateGraph, START, END

from app.graph.state import InvestigationState

from app.agents.supervisor import supervisor
from app.agents.company_agent import company_agent
from app.agents.news_agent import news_agent
from app.agents.market_agent import market_agent
from app.agents.evidence_agent import evidence_collector
from app.agents.cause_agent import cause_analyzer
from app.agents.risk_agent import risk_analyzer
from app.agents.synthesis_agent import synthesis_agent
from app.agents.audit_agent import audit_agent
from app.agents.movement_agent import movement_verification_agent as movement_verification


# ============================================================
# TRACE WRAPPER
# ============================================================

def _with_trace(
    agent_name: str,
    node_function,
):
    """
    Wrap synchronous and asynchronous nodes.

    Each node returns only its own trace entry.
    InvestigationState.merge_trace() combines entries,
    including parallel branches.
    """

    if inspect.iscoroutinefunction(node_function):

        async def async_wrapped(
            state: InvestigationState,
        ) -> Dict[str, Any]:

            result = await node_function(state)

            if result is None:
                result = {}

            result = dict(result)

            # Do NOT merge with state["trace"] here.
            # LangGraph's Annotated reducer handles that.

            result["trace"] = [
                {
                    "agent": agent_name,
                    "status": "completed",
                }
            ]

            return result

        async_wrapped.__name__ = (
            f"{agent_name}_wrapped"
        )

        return async_wrapped

    # ========================================================
    # SYNCHRONOUS NODE
    # ========================================================

    def sync_wrapped(
        state: InvestigationState,
    ) -> Dict[str, Any]:

        result = node_function(state)

        if result is None:
            result = {}

        result = dict(result)

        # Do NOT merge with state["trace"] here.
        # LangGraph's Annotated reducer handles that.

        result["trace"] = [
            {
                "agent": agent_name,
                "status": "completed",
            }
        ]

        return result

    sync_wrapped.__name__ = (
        f"{agent_name}_wrapped"
    )

    return sync_wrapped
# ============================================================
# ROUTING
# ============================================================

def movement_decision(
    state: InvestigationState,
) -> str:

    intent = state.get(
        "investigation_intent",
        "general",
    )

    movement = state.get(
        "movement_verification",
        {},
    ) or {}

    # General investigation does not require
    # movement matching.
    if intent != "cause_analysis":
        return "continue"

    requested = movement.get(
        "requested_direction"
    )

    actual = movement.get(
        "actual_direction"
    )

    verified = bool(
        movement.get(
            "verified",
            False,
        )
    )

    matches = bool(
        movement.get(
            "matches_request",
            False,
        )
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Even mismatch/unknown must continue through:
    #
    # Evidence -> Cause -> Risk -> Synthesis -> Audit
    #
    # This is required for the complete investigation trace.
    # --------------------------------------------------------

    if (
        verified
        and requested in {"up", "down"}
        and actual in {"up", "down"}
        and matches
    ):
        return "continue"

    return "mismatch"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_workflow():

    workflow = StateGraph(
        InvestigationState
    )

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    workflow.add_node(
        "supervisor",
        _with_trace(
            "supervisor",
            supervisor,
        ),
    )

    workflow.add_node(
        "company_agent",
        _with_trace(
            "company_agent",
            company_agent,
        ),
    )

    workflow.add_node(
        "news_agent",
        _with_trace(
            "news_agent",
            news_agent,
        ),
    )

    workflow.add_node(
        "market_agent",
        _with_trace(
            "market_agent",
            market_agent,
        ),
    )

    workflow.add_node(
        "movement_verification",
        _with_trace(
            "movement_agent",
            movement_verification,
        ),
    )

    workflow.add_node(
        "evidence_collector",
        _with_trace(
            "evidence_agent",
            evidence_collector,
        ),
    )

    workflow.add_node(
        "cause_analyzer",
        _with_trace(
            "cause_agent",
            cause_analyzer,
        ),
    )

    workflow.add_node(
        "risk_analyzer",
        _with_trace(
            "risk_agent",
            risk_analyzer,
        ),
    )

    workflow.add_node(
        "synthesis_agent",
        _with_trace(
            "synthesis_agent",
            synthesis_agent,
        ),
    )

    workflow.add_node(
        "audit_agent",
        _with_trace(
            "audit_agent",
            audit_agent,
        ),
    )

    # --------------------------------------------------------
    # Research
    # --------------------------------------------------------

    workflow.add_edge(
        START,
        "supervisor",
    )

    workflow.add_edge(
        "supervisor",
        "company_agent",
    )

    workflow.add_edge(
        "company_agent",
        "market_agent",
    )

    workflow.add_edge(
        "company_agent",
        "news_agent",
    )

    # Both research agents must finish before
    # movement verification.
    #
    # If your LangGraph version supports multiple incoming
    # edges as a join, this is sufficient.

    workflow.add_edge(
        "market_agent",
        "movement_verification",
    )

    workflow.add_edge(
        "news_agent",
        "movement_verification",
    )

    # --------------------------------------------------------
    # Movement -> Analysis
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "movement_verification",
        movement_decision,
        {
            "continue": "evidence_collector",
            "mismatch": "evidence_collector",
        },
    )

    # --------------------------------------------------------
    # Analysis pipeline
    # --------------------------------------------------------

    workflow.add_edge(
        "evidence_collector",
        "cause_analyzer",
    )

    workflow.add_edge(
        "cause_analyzer",
        "risk_analyzer",
    )

    workflow.add_edge(
        "risk_analyzer",
        "synthesis_agent",
    )

    workflow.add_edge(
        "synthesis_agent",
        "audit_agent",
    )

    workflow.add_edge(
        "audit_agent",
        END,
    )

    return workflow.compile()


# ============================================================
# COMPILED GRAPH
# ============================================================

graph = build_workflow()


# Backward-compatible name
workflow = graph