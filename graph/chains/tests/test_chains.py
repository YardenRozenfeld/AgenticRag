from dotenv import load_dotenv

load_dotenv()

from langchain_core.documents import Document

from graph.chains.answer_grader import GradeAnswer, answer_grader
from graph.chains.generation import generation_chain
from graph.chains.hallucination_grader import GradeHallucinations, hallucination_grader
from graph.chains.retrievel_grader import GradeDocuments, retrieval_grader
from graph.chains.router import RouteQuery, question_router
from ingestion import retriever


def test_retrieval_grader_relevant():
    question = "agent memory"
    docs = retriever.invoke(question)
    doc_txt = docs[0].page_content
    result: GradeDocuments = retrieval_grader.invoke(
        {"question": question, "document": doc_txt}
    )

    assert result.binary_score == "yes"


def test_retrieval_grader_not_relevant():
    question = "What are the approaches to prompt engineering?"
    document = (
        "The Mediterranean diet emphasizes fruits, vegetables, whole grains, "
        "and healthy fats like olive oil for improved cardiovascular health."
    )

    result: GradeDocuments = retrieval_grader.invoke(
        {"question": question, "document": document}
    )

    assert result.binary_score == "no"


def test_generation_chain():
    question = "What is agent memory?"
    docs = retriever.invoke(question)
    generation = generation_chain.invoke({"context": docs, "question": question})
    content = generation.content if hasattr(generation, "content") else generation
    assert isinstance(content, str) and len(content) > 0


def test_hallucination_grader_grounded():
    question = "agent memory"
    docs = retriever.invoke(question)
    generation = generation_chain.invoke({"context": docs, "question": question})
    content = generation.content if hasattr(generation, "content") else generation

    result: GradeHallucinations = hallucination_grader.invoke(
        {"documents": docs, "generation": content}
    )

    assert result.binary_score == "yes"


def test_hallucination_grader_not_grounded():
    docs = [
        Document(
            page_content="Photosynthesis is the process by which plants convert sunlight into food."
        )
    ]
    generation = "The capital of France is Paris, which has a population of over 2 million people."

    result: GradeHallucinations = hallucination_grader.invoke(
        {"documents": docs, "generation": generation}
    )

    assert result.binary_score == "no"


def test_answer_grader_useful():
    question = "What is agent memory?"
    generation = (
        "Agent memory refers to the mechanism by which an agent stores and retrieves "
        "information from past interactions to inform future decisions."
    )

    result: GradeAnswer = answer_grader.invoke(
        {"question": question, "generation": generation}
    )

    assert result.binary_score == "yes"


def test_answer_grader_not_useful():
    question = "What is agent memory?"
    generation = "Photosynthesis converts sunlight into glucose in plant cells."

    result: GradeAnswer = answer_grader.invoke(
        {"question": question, "generation": generation}
    )

    assert result.binary_score == "no"


def test_router_to_vectorstore():
    question = "What are the different types of agent memory?"
    result: RouteQuery = question_router.invoke({"question": question})
    assert result.datasource == "vectorstore"


def test_router_to_websearch():
    question = "Who won the 2024 US presidential election?"
    result: RouteQuery = question_router.invoke({"question": question})
    assert result.datasource == "websearch"
