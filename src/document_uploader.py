from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from typing import List
import os

def load_pdf(file_path: str) -> List[Document]:
    """extracts text and metadata from uploaded pdf"""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found at: {file_path}")

    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    return documents