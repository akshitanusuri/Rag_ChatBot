import os
import traceback

from src.document_uploader import load_pdf
from src.chunking import document_chunks
from src.vector_db import build_vector_store, get_vector_store
from src.LangGraphOrchestrator import graph_app


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def build_rag(pdf_path):

    section("STEP 1 : LOAD PDF")

    docs = load_pdf(pdf_path)
    print(f"Pages loaded : {len(docs)}")

    section("STEP 2 : CHUNKING")

    chunks = document_chunks(docs)
    print(f"Chunks created : {len(chunks)}")

    section("STEP 3 : BUILD VECTOR STORE")

    build_vector_store(chunks)

    print("Vector store ready")


def test_retrieval(query):

    section("VECTOR DB RETRIEVAL TEST")

    try:
        vectorstore = get_vector_store()

        results = vectorstore.similarity_search_with_score(query, k=3)

        if not results:
            print("No results found in vector DB")
            return

        for i, (doc, score) in enumerate(results):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Score: {score}")
            print(doc.page_content[:300])

    except Exception:
        print("Retrieval failed")
        print(traceback.format_exc())


def run_query(query, thread_id):

    section(f"QUERY : {query}")

    try:
        state = {
            "query": query,
            "thread_id": thread_id
        }

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        result = graph_app.invoke(state, config=config)

        print("ANSWER :")
        print(result.get("draft_answer"))

        return result

    except Exception:
        print("Graph error")
        print(traceback.format_exc())
        return None


def test_hitl():

    section("HITL TEST")

    query = "My router is smoking and I want refund"
    thread_id = "hitl_test"

    result = run_query(query, thread_id)

    try:
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        snapshot = graph_app.get_state(config)

        if result and result.get("escalate", False):

            print("HITL Triggered")
            print("Injecting Human Response")

            graph_app.update_state(
                config,
                {
                    "human_response": "Refund approved and apology sent."
                },
                as_node="hitl_wait"
            )

            final = graph_app.invoke(None, config=config)

            print("FINAL OUTPUT :")
            print(final.get("draft_answer"))

        else:
            print("HITL not triggered")

    except Exception:
        print("HITL error")
        print(traceback.format_exc())


def test_normal_queries():

    section("NORMAL QUERY TESTS")

    queries = [
        "How do I reset my router?",
        "What is refund policy?",
        "How to fix slow internet?",
        "What if router not working?",
        "What if device overheats?"
    ]

    for i, q in enumerate(queries):
        run_query(q, thread_id=f"test_{i}")


if __name__ == "__main__":

    print("Starting Test Pipeline")

    pdf_path = "dummy_manual.pdf"

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found")

    build_rag(pdf_path)

    test_retrieval("reset router")

    test_normal_queries()

    test_hitl()

    section("DONE")

    print("Pipeline executed successfully")