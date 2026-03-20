from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser

from graph.chains.generation import generation_chain
from graph.state import GraphState


def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    generation = generation_chain.invoke({"context": documents, "question": question})
    if hasattr(generation, "content"):
        generation = generation.content

    return {"documents": documents, "question": question, "generation": generation}
