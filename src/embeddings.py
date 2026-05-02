from langchain_community.embeddings import HuggingFaceBgeEmbeddings

def get_embedding_model():
    embeddings = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )
    return embeddings