# 📘 Technical Documentation  
## 🤖 RAG-Based Customer Support Assistant (LangGraph + HITL System)

---

## 1. Introduction

This project implements a **Retrieval-Augmented Generation (RAG)** based customer support system that answers user queries using uploaded PDF documents.

Instead of relying only on a Large Language Model, the system first retrieves relevant information from a knowledge base and then generates responses based on that context.

The system is designed for:
- Accurate document-based question answering
- Reduced hallucination from LLMs
- Safe escalation using Human-in-the-Loop (HITL)

---

## 2. System Overview

The system is built as a **multi-layer AI pipeline** consisting of:

- Frontend (Streamlit Chat UI)
- Backend (FastAPI)
- Workflow Engine (LangGraph)
- Vector Database (ChromaDB)
- LLM (for response generation)

Each layer is modular and communicates through API-based interactions.

---

## 3. End-to-End Workflow

### 📥 Step 1: Document Ingestion
- User uploads PDF files through Streamlit UI
- Backend extracts text from PDFs
- Text is cleaned and normalized
- Document is split into smaller chunks

---

### 🧠 Step 2: Embedding Generation
- Each text chunk is converted into a vector representation
- Embeddings capture semantic meaning of text
- Vectors are stored in ChromaDB for later retrieval

---

### 🔎 Step 3: Query Processing
- User submits a query via chat interface
- Query is converted into embedding vector
- Similar chunks are retrieved from vector database

---

### 🤖 Step 4: Response Generation
- Retrieved context + user query is passed to LLM
- LLM generates a context-grounded response
- System ensures response is based only on retrieved data

---

### ⚖️ Step 5: Decision Layer
- System evaluates response quality and confidence
- If response is valid → send to user
- If response is uncertain → trigger HITL flow

---

### 👨‍💻 Step 6: Human-in-the-Loop (HITL)
- Workflow is paused using LangGraph state control
- Query is sent to admin dashboard
- Human agent provides final response
- System resumes execution from paused state

---

## 4. System Architecture Design

The architecture is divided into four major components:

### 1. UI Layer
- Built using Streamlit
- Handles chat interface and file uploads
- Maintains session state using thread ID

---

### 2. API Layer
- Built using FastAPI
- Exposes endpoints for chat, upload, and HITL resolution
- Communicates with LangGraph workflow engine

---

### 3. AI Workflow Layer
- Managed using LangGraph
- Controls sequence of operations:
  - retrieval → generation → validation → routing
- Maintains conversation state across requests

---

### 4. Knowledge Layer
- Uses ChromaDB for vector storage
- Stores embeddings of document chunks
- Enables fast semantic search

---

## 5. Key Modules

### 📄 Document Processor
- Extracts text from PDFs
- Removes noise like headers and page numbers
- Prepares clean text for chunking

---

### ✂️ Chunking Engine
- Splits text into overlapping segments
- Ensures continuity between chunks
- Optimized for embedding quality

---

### 🧠 Embedding System
- Converts text and queries into dense vectors
- Ensures semantic similarity matching

---

### 🔎 Retrieval System
- Finds most relevant chunks using cosine similarity
- Returns top-k relevant results for LLM context

---

### 🤖 LLM Module
- Generates final response using retrieved context
- Prevents hallucination by restricting external knowledge

---

### 🔁 LangGraph Controller
- Manages state-based execution flow
- Supports pause/resume execution for HITL
- Maintains thread-based memory

---

### ⚖️ Decision Engine
- Evaluates whether response is safe and complete
- Routes output to user or HITL system

---

## 6. Data Flow

### 📥 Ingestion Flow
PDF Upload → Text Extraction → Cleaning → Chunking → Embedding → ChromaDB Storage

---

### 💬 Query Flow
User Query → Embedding → Vector Search → Context Retrieval → LLM Generation → Decision Layer → Output / HITL

---

## 7. API Design

### 📌 Chat API
`POST /chat`

Request:
```json
{
  "query": "How do I reset my password?",
  "thread_id": "abc123"
}
```

Response:
```json
{
  "status": "success",
  "answer": "Go to settings → reset password option"
}
```

---

### 📌 Upload API
`POST /upload`
- Accepts PDF files
- Returns ingestion status

---

### 📌 HITL API
`POST /hitl/resolve/{thread_id}`
- Accepts human response
- Resumes paused workflow

---

## 8. Error Handling

- If no relevant chunks are found → escalate to HITL
- If LLM fails → retry mechanism with fallback
- If invalid input → request validation at API level
- If workflow fails → restore state using LangGraph checkpoint

---

## 9. Design Principles

- RAG ensures factual and grounded responses
- LangGraph enables controlled execution flow
- HITL ensures human fallback safety
- Modular design allows easy scaling
- Vector search improves semantic accuracy over keyword search

---

## 10. Future Improvements

- Streaming responses for real-time chat experience
- Authentication system for users and admin dashboard
- Cloud vector DB migration (Pinecone/Weaviate)
- Feedback loop to improve response quality
- Multi-language support for global users

---

## 11. Summary

This system is a production-style implementation of a **RAG-based AI assistant** combining:
- Document retrieval
- LLM generation
- Workflow orchestration
- Human fallback safety

It is designed to be scalable, modular, and reliable for real-world customer support applications.
