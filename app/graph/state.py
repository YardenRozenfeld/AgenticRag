from typing import Annotated, List, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        web_search: whether to add search
        documents: list of documents
        messages: conversation history (auto-accumulated via add_messages reducer)
    """

    question: str
    generation: str
    web_search: bool
    documents: List
    messages: Annotated[list[AnyMessage], add_messages]
