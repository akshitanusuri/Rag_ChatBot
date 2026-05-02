# ⚙️ Low-Level Design (LLD): RAG-Based Customer Support Assistant

## 1. Component-Level Breakdown

### 📌 Frontend Layer (Streamlit Chat UI)
- Handles user interaction through a chat interface.
- Maintains session state using `st.session_state` (thread_id + chat history).
- Sends user queries and file uploads to backend APIs.
- Renders assistant responses in conversational format (chat bubbles).

---

### 📌 Backend API Layer (FastAPI)
- Acts as the communication bridge between UI and AI pipeline.
- Exposes endpoints:
  - `/chat` → process user query
  - `/upload` → ingest PDFs
  - `/hitl/resolve` → resume human-handled threads
- Sends structured request payloads to LangGraph engine.

---

### 📌 RAG Pipeline Controller (LangGraph)
- Manages full execution flow as a state-based graph.
- Maintains conversation state using `thread_id`.
- Controls transition between:
  - retrieval → generation → validation → response or escalation

---

### 📌 Document Ingestion Module
- Accepts PDF uploads from user.
- Extracts raw text using PDF parsing utilities.
- Performs cleaning:
  - removes headers, page numbers, empty lines
- Stores processed text for chunking stage.

---

### 📌 Chunking & Preprocessing Module
- Splits documents into overlapping text segments.
- Ensures semantic continuity across chunks.
- Prepares structured inputs for embedding generation.

---

### 📌 Embedding Generation Module
- Converts each chunk into vector representation.
- Uses embedding model to transform text → numeric vectors.
- Produces consistent vector dimensions for storage.

---

### 📌 Vector Database Layer (ChromaDB)
- Stores embeddings along with metadata (source file, page number).
- Supports semantic similarity search using cosine distance.
- Returns top-K most relevant chunks for a query.

---

### 📌 Retrieval Module
- Converts user query into embedding vector.
- Performs similarity search on vector database.
- Applies filtering to remove irrelevant or low-score results.
- Outputs ranked context chunks for LLM.

---

### 📌 LLM Response Generator
- Takes retrieved context + user query as input prompt.
- Generates grounded response only from provided context.
- Prevents hallucination by restricting external knowledge usage.

---

### 📌 Decision & Routing Module
- Evaluates whether generated response is safe and sufficient.
- Decision factors:
  - missing retrieval context
  - weak similarity scores
  - ambiguous query intent
- Routes execution to:
  - final response OR
  - HITL escalation

---

### 📌 Human-in-the-Loop (HITL) Module
- Triggered when system cannot confidently respond.
- Stores conversation state and pauses workflow.
- Sends request to admin dashboard for manual resolution.
- Injects human response back into active thread.

---

## 2. Internal Data Structures

### 📄 Document Object
```json
{
  "text": "Steps to reset your password...",
  "metadata": {
    "file_name": "guide.pdf",
    "page": 2
  }
}
```

---

### 🧠 Vector Representation
- Float array generated from embedding model
- Represents semantic meaning of text chunks

---

### 💬 Chat State Object (Session Memory)
```python
{
  "thread_id": "abc123",
  "user_query": "...",
  "retrieved_context": [],
  "final_answer": "",
  "status": "processing | completed | hitl_pending"
}
```

---

### 🔁 API Response Format
```json
{
  "status": "success",
  "answer": "Final grounded response",
  "thread_id": "abc123"
}
```

---

## 3. Execution Workflow (System Runtime)

### Step 1: User Interaction
- User sends query from Streamlit chat UI.
- Request is forwarded to FastAPI backend.

---

### Step 2: Retrieval Phase
- Query is embedded into vector space.
- ChromaDB retrieves top matching document chunks.
- Irrelevant results are filtered out.

---

### Step 3: Generation Phase
- Retrieved context + query passed to LLM.
- LLM generates a response strictly based on context.

---

### Step 4: Validation Phase
- System checks:
  - retrieval quality
  - response completeness
  - query complexity
- If valid → proceed to output  
- If uncertain → escalate

---

### Step 5: HITL Flow (if triggered)
- Execution paused using LangGraph state suspension.
- Thread stored in memory.
- Admin reviews query in dashboard.
- Human response injected back into system.
- Workflow resumes from last state.

---

## 4. Routing Logic (Decision Engine)

The system uses simple rule-based + retrieval-based logic:

- If **no context retrieved** → escalate
- If **similarity score is low** → escalate
- If **query is ambiguous or sensitive** → escalate
- Otherwise → generate final response

This ensures safe and grounded outputs.

---

## 5. API Design Overview

### 📌 Chat API
`POST /chat`
```json
{
  "query": "How do I reset password?",
  "thread_id": "123"
}
```

Response:
```json
{
  "status": "ok",
  "answer": "Go to settings → reset password"
}
```

---

### 📌 File Upload API
`POST /upload`
- Accepts PDF file
- Returns ingestion status

---

### 📌 HITL Resolve API
`POST /hitl/resolve/{thread_id}`
- Accepts human response
- Resumes paused workflow

---

## 6. Error Handling Strategy

- **No retrieval results:** system directly escalates to HITL
- **LLM failure:** retry mechanism with fallback escalation
- **Invalid input:** request validation at API level
- **Workflow crash:** state recovery using LangGraph checkpointing

---

## 7. Key Design Philosophy

- RAG is used to ensure **grounded responses**
- LangGraph ensures **controlled execution flow**
- HITL ensures **human safety net**
- Modular architecture ensures **easy scaling and debugging**
- Streamlit ensures **fast interactive UI development**
