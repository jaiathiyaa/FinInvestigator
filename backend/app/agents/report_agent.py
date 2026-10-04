from app.graph.state import InvestigationState


def report_agent(state: InvestigationState) -> InvestigationState:

    company = state["company"]

    company_data = state.get("company_data", {})
    news_data = state.get("news_data", {})
    market_data = state.get("market_data", {})

    report = f"""
# Financial Investigation Report

## Company

Company: {company}

Description:
{company_data.get("description", "No information available.")}


## Recent News

"""

    articles = news_data.get("articles", [])

    if articles:
        for article in articles:
            report += f"- {article}\n"
    else:
        report += "No news information collected.\n"

    report += """

## Market Information

"""

    market_information = market_data.get(
        "market_information",
        []
    )

    if market_information:
        for item in market_information:
            report += f"- {item}\n"
    else:
        report += "No market information collected.\n"

    report += """

## Investigation Status

The investigation was completed using the available
company, news and market investigation agents.
"""

    return {
        **state,
        "report": report
    }