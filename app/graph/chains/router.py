from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import get_settings


class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["websearch", "vectorstore"] = Field(
        description="Given a user question choose to route it to web search or a vectorstore."
    )


llm = ChatOpenAI(model=get_settings().grader_model, temperature=0)
structured_llm_router = llm.with_structured_output(RouteQuery, method="function_calling")

system = """You are an expert at routing a user question to a vectorstore or web search.
The vectorstore contains documents about agents, prompt engineering, and adversarial attacks on LLMs.
Use the vectorstore for questions on these topics. For all other questions, use web search."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router
