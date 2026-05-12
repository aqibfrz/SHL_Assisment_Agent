from src.rag.embeddings import get_embedding
from src.rag.vector_store import search_index

def retrieve_assessments(query, k=5):
    query_vec = get_embedding(query)
    return search_index(query_vec, k)