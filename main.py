import os
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.document_uploader import load_pdf
from src.chunking import document_chunks
from src.vector_db import build_vector_store, get_vector_store
from src.LangGraphOrchestrator import graph_app


load_dotenv()

app = FastAPI(
    title="RAG HITL Customer Support Assistant",
    description="Backend APIs for Streamlit Frontend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class ChatRequest(BaseModel):
    query: str
    thread_id: str


class ResolveRequest(BaseModel):
    human_response: str


@app.post("/api/v1/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = f"temp_{file.filename}"

    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")

        with open(file_path, "wb") as f:
            f.write(await file.read())

        print("PDF saved at:", file_path)

        docs = load_pdf(file_path)
        print("Pages loaded:", len(docs))

        chunks = document_chunks(docs)
        print("Chunks created:", len(chunks))

        if len(chunks) == 0:
            raise Exception("No chunks created from PDF")

        build_vector_store(chunks)
        print("Chunks added to vector DB")

        return {
            "status": "success",
            "message": f"{file.filename} uploaded successfully"
        }

    except Exception as e:
        print("\nUPLOAD ERROR:")
        print(traceback.format_exc())   # 🔥 REAL ERROR WILL SHOW HERE

        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):

    store = get_vector_store()
    data = store.get()

    if len(data.get("ids", [])) == 0:
        raise HTTPException(status_code=400, detail="No documents uploaded yet")

    state = {
        "query": request.query,
        "thread_id": request.thread_id
    }

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    result = graph_app.invoke(state, config=config)

    if result.get("escalate", False):
        return {
            "status": "pending_hitl",
            "message": "Escalated to human support",
            "thread_id": request.thread_id
        }

    return {
        "status": "ok",
        "answer": result.get("draft_answer", "No response")
    }


@app.post("/api/v1/hitl/resolve/{thread_id}")
async def resolve_hitl(thread_id: str, request: ResolveRequest):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    graph_app.update_state(
        config,
        {
            "human_response": request.human_response
        },
        as_node="hitl_wait"
    )

    result = graph_app.invoke(None, config=config)

    return {
        "status": "resolved",
        "final_answer": result.get("draft_answer", "Resolved")
    }


@app.get("/api/v1/stats")
async def get_stats():

    try:
        store = get_vector_store()
        data = store.get()
        count = len(data.get("ids", []))

        return {
            "documents": count,
            "chunks": count,
            "embeddings": count
        }

    except:
        return {
            "documents": 0,
            "chunks": 0,
            "embeddings": 0
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )