from typing import Any, Dict

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document

from graph.state import GraphState

web_search_tool = TavilySearchResults(k=3)


def web_search(state: GraphState) -> Dict[str, Any]:
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents", [])

    results = web_search_tool.invoke({"query": question})
    web_results = [
        Document(page_content=result["content"], metadata={"source": result["url"]})
        for result in results
    ]
    documents = documents + web_results

    return {"documents": documents, "question": question}
