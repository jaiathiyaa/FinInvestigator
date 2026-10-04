from langgraph.graph import StateGraph , START , END

from app.graph.state import InvestigationState

from app.agents.report_agent import report_agent
from app.agents.company_agent import company_agent
from app.agents.news_agent import news_agent
from app.agents.market_agent import market_agent
from app.agents.supervisor import supervisor

def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("supervisor", supervisor)
    graph.add_node("company_agent", company_agent)
    graph.add_node("news_agent", news_agent)
    graph.add_node("market_agent", market_agent)
    graph.add_node("report_agent", report_agent)

    graph.add_edge(START, "supervisor")

    graph.add_edge(
        "supervisor",
        "company_agent"
    )

    graph.add_edge(
        "supervisor",
        "news_agent"
    )

    graph.add_edge(
        "supervisor",
        "market_agent"
    )

    graph.add_edge(
        "company_agent",
        "report_agent"
    )
    graph.add_edge(
        "news_agent",
        "report_agent"
    )
    graph.add_edge(
        "market_agent",
        "report_agent"
    )

    graph.add_edge(
        "report_agent",
        END
    )

    return graph.compile()