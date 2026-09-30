from typing import TypedDict, Any
from langgraph.graph import StateGraph, START , END
from langchain_openai import ChatOpenAI
from app.core.config import setting
from app.mcp.client import (
    call_search_finance,
    call_search_news,
    call_search_web
)

llm = ChatOpenAI(
    api_key=setting.openai_api_key,
    model="gpt-4o-mini",
    temperature=0
)

class InvestigationState(TypedDict):
    query: str
    web_results : Any
    news_results : Any
    finance_results: Any
    response: str

async def research_node(state: InvestigationState):
    query = state["query"]

    web_results = await call_search_web(query)
    news_results = await call_search_news(query)
    finance_results = await call_search_finance(query)

    return {
        "web_results" : web_results,
        "news_results" : news_results,
        "finance_results" : finance_results
    }

def supervisor_node(state: InvestigationState):
    query = state['query']
    
    prompt = f"""
        You are a supervisor of a financial investigation system.
        
        User Question : 
        {query}

        Explain what kind of financial investigation should be performed.
    """
    result = llm.invoke(prompt)
    
    return {
        "response" : result.content
    }

def build_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("research",research_node)

    graph.add_edge(START,"research")
    graph.add_edge("research",END)

    return graph.compile()

investigation_graph = build_graph()