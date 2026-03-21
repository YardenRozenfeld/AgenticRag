from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.chains.generation import generation_chain
from app.graph.state import GraphState


def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    generation = generation_chain.invoke({"context": documents, "question": question})
    if hasattr(generation, "content"):
        generation = generation.content

    return {
        "documents": documents,
        "question": question,
        "generation": generation,
        "messages": [
            HumanMessage(content=question),
            AIMessage(content=generation),
        ],
    }
