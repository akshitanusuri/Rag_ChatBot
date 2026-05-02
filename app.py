import streamlit as st
import requests
import uuid

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RAG Customer Support Assistant",
    page_icon="🤖",
    layout="wide"
)

# ---------------- SESSION ----------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- STYLES ----------------
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🤖 RAG Customer Support Assistant")
st.caption("FastAPI + LangGraph + HITL + Streamlit Dashboard")

# ---------------- STATS ----------------
col1, col2, col3 = st.columns(3)

try:
    response = requests.get(f"{BACKEND_URL}/api/v1/stats")
    stats = response.json()
except:
    stats = {"documents": 0, "chunks": 0, "embeddings": 0}

col1.metric("📄 Documents", stats.get("documents", 0))
col2.metric("🧩 Chunks", stats.get("chunks", 0))
col3.metric("🧠 Embeddings", stats.get("embeddings", 0))

st.divider()

# ---------------- MAIN LAYOUT ----------------
left, center, right = st.columns([1, 2, 1])

# -------- LEFT PANEL (FILES + UPLOAD) --------
with left:
    st.subheader("📂 Knowledge Base")

    # Show uploaded files
    try:
        res = requests.get(f"{BACKEND_URL}/api/v1/files")
        files_data = res.json()
        files = files_data.get("files", [])

        if files:
            for f in files:
                st.write(f"📄 {f}")
        else:
            st.info("No files uploaded yet")
    except:
        st.warning("Cannot load file list")

    st.divider()

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file is not None:
        if st.button("Upload PDF"):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            }

            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/upload",
                    files=files
                )

                response.raise_for_status()
                data = response.json()

                st.success(data.get("message"))

            except Exception as e:
                st.error(f"Upload failed: {e}")

# -------- CENTER PANEL (CHAT) --------
with center:
    st.subheader("💬 Chat Assistant")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    query = st.chat_input("Ask your question...")

    if query:
        st.session_state.chat_history.append(
            {"role": "user", "content": query}
        )

        with st.chat_message("user"):
            st.write(query)

        payload = {
            "query": query,
            "thread_id": st.session_state.thread_id
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/chat",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            if data.get("status") == "pending_hitl":
                answer = f"⚠️ Escalated to Human Support\n\nThread ID: {st.session_state.thread_id}"
            else:
                answer = data.get("answer", "No response")

        except Exception as e:
            answer = f"Backend Error: {e}"

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )

        with st.chat_message("assistant"):
            st.write(answer)

# -------- RIGHT PANEL (WORKFLOW + HITL) --------
with right:
    st.subheader("⚙️ Workflow")

    st.markdown("""
    **Input Node**  
    User Query  

    ↓  

    **Processing Node**  
    Retrieval + LLM  

    ↓  

    **Output Node**  
    Generated Answer  

    ↓  

    **HITL Escalation**  
    Triggered if needed  
    """)

    st.divider()

    st.subheader("👨‍💻 Human Support")

    thread_id = st.text_input("Thread ID")
    human_reply = st.text_area("Human Response")

    if st.button("Submit Response"):
        payload = {
            "human_response": human_reply
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/hitl/resolve/{thread_id}",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            st.success(data.get("final_answer"))

        except Exception as e:
            st.error(f"Error: {e}")