from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.graph.chains.answer_grader import answer_grader
from app.graph.chains.hallucination_grader import hallucination_grader
from app.graph.chains.router import question_router
from app.graph.consts import GENERATE, GRADE_DOCUMENTS, RETRIEVE, WEBSEARCH
from app.graph.nodes.generate import generate
from app.graph.nodes.grade_documents import grade_documents
from app.graph.nodes.retrieve import retrieve
from app.graph.nodes.web_search import web_search
from app.graph.state import GraphState


def route_question(state: GraphState) -> str:
    print("---ROUTE QUESTION---")
    question = state["question"]
    source = question_router.invoke({"question": question})
    if source.datasource == "websearch":
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return WEBSEARCH
    print("---ROUTE QUESTION TO RAG---")
    return RETRIEVE


def decide_to_generate(state: GraphState) -> str:
    print("---ASSESS GRADED DOCUMENTS---")
    if state["web_search"]:
        print("---DECISION: NOT ALL DOCUMENTS ARE RELEVANT, INCLUDE WEB SEARCH---")
        return WEBSEARCH
    print("---DECISION: GENERATE---")
    return GENERATE


def grade_generation_v_documents_and_question(state: GraphState) -> str:
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )

    if score.binary_score == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        if score.binary_score == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
        return "not useful"

    print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
    return "not supported"


def build_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    workflow = StateGraph(GraphState)

    workflow.add_node(RETRIEVE, retrieve)
    workflow.add_node(GRADE_DOCUMENTS, grade_documents)
    workflow.add_node(GENERATE, generate)
    workflow.add_node(WEBSEARCH, web_search)

    workflow.add_conditional_edges(
        START,
        route_question,
        {WEBSEARCH: WEBSEARCH, RETRIEVE: RETRIEVE},
    )
    workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
    workflow.add_conditional_edges(
        GRADE_DOCUMENTS,
        decide_to_generate,
        {WEBSEARCH: WEBSEARCH, GENERATE: GENERATE},
    )
    workflow.add_edge(WEBSEARCH, GENERATE)
    workflow.add_conditional_edges(
        GENERATE,
        grade_generation_v_documents_and_question,
        {
            "not supported": GENERATE,
            "useful": END,
            "not useful": WEBSEARCH,
        },
    )

    return workflow.compile(checkpointer=checkpointer)
