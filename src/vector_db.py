import os
import shutil
from typing import List
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.embeddings import get_embedding_model

db_path = os.path.join(os.getcwd(), "rag_db")

COLLECTION_NAME = "insurance_support_kb"


def build_vector_store(chunks: List[Document]):

    # 🔴 FIX: clear old DB (prevents empty/corrupt retrieval issues)
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    embeddings = get_embedding_model()

    vectorstore = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    vectorstore.add_documents(chunks)

    # 🔴 ensure data is saved
    vectorstore.persist()

    print("DB Path :", db_path)
    print("Chunks Added :", len(chunks))

    return vectorstore


def get_vector_store():

    embeddings = get_embedding_model()

    vectorstore = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    # 🔴 DEBUG: helps confirm DB is being loaded
    print("Loading vector DB from:", db_path)

    return vectorstore