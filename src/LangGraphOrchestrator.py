import os
from typing import List, Any, Dict, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.vector_db import get_vector_store
from src.router import routing_logic

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


# state object (so that state travels between all graph nodes.)
class AgentState(TypedDict):
    query: str
    thread_id: str
    context: List[Any]
    answer: str
    confidence: float
    escalate: bool
    human_response: Optional[str]
    reasoning: Optional[Dict[str, Any]]
    draft_answer: str


# node 1: retrieve relevant chunks from document
def retrieve_chunks(state: AgentState):
    """searches chromadb for relevant chunks according to user query"""

    query = state["query"]

    vectorstore = get_vector_store()

    results = vectorstore.similarity_search_with_score(
        query,
        k=5
    )

    # 🔴 DEBUG (IMPORTANT)
    print("\n🔍 Query:", query)
    print("🔍 Raw Results:", results)

    docs = [
        doc for doc, score in results
    ]

    print("🔍 Retrieved Docs Count:", len(docs))

    return {
        "context": docs
    }


# node 2: generate answer
def generate_draft_node(state: AgentState):
    """uses retrieved chunks and llm to generate answer"""

    query = state["query"]
    context = state.get("context", [])

    if not context:
        return {
            "draft_answer": "Sorry, I could not find relevant answer in the knowledge base.",
            "confidence": 0.0,
            "reasoning": {}
        }

    context_text = "\n\n".join(
        [doc.page_content for doc in context]
    )

    try:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in .env file")

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            groq_api_key=api_key   # FIXED
        )

        prompt = ChatPromptTemplate.from_template(
            """
            You are a professional customer support assistant.

            Answer ONLY from given context.

            If answer not found in context,
            say politely information unavailable.

            Context:
            {context}

            User Question:
            {query}

            Answer:
            """
        )

        chain = prompt | llm

        response = chain.invoke(
            {
                "context": context_text,
                "query": query
            }
        )

        answer = response.content

        sources = []

        for doc in context:
            file_name = os.path.basename(
                doc.metadata.get("source", "Unknown File")
            )

            page = doc.metadata.get("page", 0) + 1

            sources.append(f"{file_name} (Page {page})")

        if sources:
            answer += "\n\nSources:\n"
            answer += "\n".join([f"- {s}" for s in set(sources)])

        return {
            "draft_answer": answer,
            "confidence": 0.90,
            "reasoning": {
                "chunks_used": len(context)
            }
        }

    except Exception as e:
        return {
            "draft_answer": f"System Error : {str(e)}",
            "confidence": 0.0,
            "reasoning": {}
        }


# node 3: evaluate rules
def evaluate_rules_node(state: AgentState):
    """decides whether human support needed"""

    route = routing_logic(state)

    if route == "escalate":
        return {"escalate": True}

    return {"escalate": False}


# node 4: wait for human
def hitl_wait_node(state: AgentState):
    """pause graph for human support"""
    return state


# node 5: final output
def finalise_output_node(state: AgentState):

    if state.get("human_response"):
        final = state["human_response"]

    elif state.get("escalate"):
        final = "Your query has been escalated to support agent."

    else:
        final = state["draft_answer"]

    return {
        "draft_answer": final
    }


# build graph
def build_graph():

    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_chunks)
    workflow.add_node("generate", generate_draft_node)
    workflow.add_node("evaluate", evaluate_rules_node)
    workflow.add_node("hitl_wait", hitl_wait_node)
    workflow.add_node("finalise", finalise_output_node)

    workflow.set_entry_point("retrieve")

    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "evaluate")

    # FIXED ROUTING (IMPORTANT)
    workflow.add_conditional_edges(
        "evaluate",
        lambda state: "escalate" if state.get("escalate") else "respond",
        {
            "respond": "finalise",
            "escalate": "hitl_wait"
        }
    )

    workflow.add_edge("hitl_wait", "finalise")
    workflow.add_edge("finalise", END)

    memory = MemorySaver()

    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["hitl_wait"]
    )

    return app


graph_app = build_graph()