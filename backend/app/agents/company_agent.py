from app.graph.state import InvestigationState
from app.mcp.client import call_search_web


async def company_agent(
    state: InvestigationState
) -> InvestigationState:

    company = state["company"]

    print(f"[Company Agent] Investigating {company}")

    query = f"{company} company overview business products financial information"

    try:
        result = await call_search_web(query)

        print("[Company Agent] MCP response received")

        return {
            "company_data": {
                "query": query,
                "result": result,
                "agent": "company_agent",
                "source_type": "web"
            }
        }

    except Exception as e:

        print(f"[Company Agent] Error: {e}")

        return {
            "company_data": {
                "query": query,
                "result": None,
                "agent": "company_agent",
                "source_type": "web",
                "error": str(e)
            }
        }